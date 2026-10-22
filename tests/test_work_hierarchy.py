"""Complete hierarchy identity, empty branches and reference selection behavior.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.domain.work_hierarchy import LineKey, SectionKey, WorkHierarchy

# Exact synthetic plant/section ancestry for orphan and duplicate-key boundaries.
SECTION = SectionKey("P", "S")
# Exact synthetic plant/section/line ancestry for branch identity boundaries.
LINE = LineKey("P", "S", "L")
# Exact synthetic station ancestry; repeated station captions on other branches remain
# distinct.
STATION = StationKey("P", "S", "L", "001")
# Immutable synthetic work catalog with exact workers/stations/shifts for hierarchy
# validation.
WORK = WorkCatalog("project", (WorkerEntry("w"),), (STATION,), ("Day",))
# Immutable synthetic complete hierarchy, including the empty branches/shifts needed by
# these tests.
HIERARCHY = WorkHierarchy(WORK, ("P",), (SECTION,), (LINE,))


def test_reference_child_queries_preserve_empty_parents_and_order() -> None:
    """Replay captured original queries without access to the reference runtime.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/work_hierarchy_reference.json").read_text()
    )
    work = WorkCatalog(
        "project",
        (),
        tuple(StationKey(*row) for row in fixture["stations"]),
        tuple(fixture["shifts"]),
    )
    hierarchy = WorkHierarchy(
        work,
        tuple(fixture["plants"]),
        tuple(SectionKey(*row) for row in fixture["sections"]),
        tuple(LineKey(*row) for row in fixture["lines"]),
    )
    for query in fixture["queries"]:
        args = query["args"]
        match query["method"]:
            case "getPlants":
                actual = list(hierarchy.plants)
            case "getSections":
                actual = [key.section_name for key in hierarchy.sections_in(*args)]
            case "getLines":
                actual = [
                    key.line_name for key in hierarchy.lines_in(SectionKey(*args))
                ]
            case "getStations":
                actual = [
                    key.station_id for key in hierarchy.stations_in(LineKey(*args))
                ]
            case "getShifts":
                actual = list(hierarchy.work.shifts)
            case _:
                pytest.fail("Unexpected fixture query")
        assert actual == query["expected"], query
    assert len(hierarchy.work.available_workplaces()) == 6


def test_empty_hierarchy_and_empty_parents_are_valid() -> None:
    """Keep independently existing parents even when there is no complete workplace.

    Args:
        None.

    Returns:
        None.
    """
    empty = WorkHierarchy(WorkCatalog("p"))
    assert empty.plants == empty.sections == empty.lines == ()
    assert empty.work.available_workplaces() == ()
    plant_only = replace(empty, plants=("P",))
    assert plant_only.sections_in("P") == ()
    section_only = replace(plant_only, sections=(SECTION,))
    assert section_only.lines_in(SECTION) == ()
    line_only = replace(section_only, lines=(LINE,))
    assert line_only.stations_in(LINE) == ()


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"plants": ()}, "missing plant"),
        ({"sections": ()}, "missing section"),
        ({"lines": ()}, "missing line"),
        ({"sections": (SectionKey("Other", "S"),)}, "missing plant"),
        ({"lines": (LineKey("P", "Other", "L"),)}, "missing section"),
        ({"lines": (LineKey("P", "S", "Other"),)}, "missing line"),
    ],
)
def test_orphans_fail_before_snapshot_publication(changes: dict, message: str) -> None:
    """Never invent a missing ancestor or silently reparent a station.

    Args:
        changes: Explicit malformed field overrides for the immutable boundary object
            under test.
        message: Expected diagnostic or literal notification content asserted by the
            test.

    Returns:
        None.
    """
    with pytest.raises(ValueError, match=message):
        replace(HIERARCHY, **changes)
    assert HIERARCHY.stations_in(LINE) == (STATION,)


def test_exact_ancestry_allows_repeated_names_without_cross_branch_results() -> None:
    """Equal section/line/station names under different plants remain separate.

    Args:
        None.

    Returns:
        None.
    """
    other_section = replace(SECTION, plant_name="Other")
    other_line = replace(LINE, plant_name="Other")
    other_station = replace(STATION, plant_name="Other")
    hierarchy = WorkHierarchy(
        replace(WORK, stations=(other_station, STATION)),
        ("P", "Other"),
        (SECTION, other_section),
        (LINE, other_line),
    )
    assert hierarchy.sections_in("P") == (SECTION,)
    assert hierarchy.lines_in(other_section) == (other_line,)
    assert hierarchy.stations_in(other_line) == (other_station,)
    assert hierarchy.stations_in(LINE) == (STATION,)
    for parent in ("p", "P ", "unknown"):
        with pytest.raises(KeyError):
            hierarchy.sections_in(parent)
    with pytest.raises(KeyError):
        hierarchy.lines_in(replace(SECTION, section_name="missing"))
    with pytest.raises(KeyError):
        hierarchy.stations_in(replace(LINE, line_name="missing"))


def test_duplicate_parents_and_untyped_records_fail() -> None:
    """Require one unambiguous identity at every hierarchy level.

    Args:
        None.

    Returns:
        None.
    """
    for field, value in (("plants", "P"), ("sections", SECTION), ("lines", LINE)):
        with pytest.raises(ValueError, match="unique"):
            replace(HIERARCHY, **{field: (value, value)})
    for field in ("sections", "lines"):
        with pytest.raises(ValueError, match="typed"):
            replace(HIERARCHY, **{field: (None,)})
    with pytest.raises(ValueError, match="typed"):
        replace(HIERARCHY, work=None)


@pytest.mark.parametrize("invalid", ["", " \t", None, 1, True])
def test_parent_identifiers_are_not_coerced(invalid: object) -> None:
    """Reject missing or untyped keys while preserving exact valid spelling.

    Args:
        invalid: Deliberately invalid typed boundary value; must fail without partial
            state changes.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        replace(HIERARCHY, plants=(invalid,))
    for value, fields in (
        (SECTION, ("plant_name", "section_name")),
        (LINE, ("plant_name", "section_name", "line_name")),
    ):
        for field in fields:
            with pytest.raises(ValueError):
                replace(value, **{field: invalid})
    assert SectionKey(" P ", " S ").plant_name == " P "


def test_snapshot_is_frozen_and_projects_do_not_share_mutable_collections() -> None:
    """Copy incoming collections; published hierarchy remains project-owned.

    Args:
        None.

    Returns:
        None.
    """
    plants, sections, lines = ["P"], [SECTION], [LINE]
    hierarchy = WorkHierarchy(WORK, plants, sections, lines)
    plants.clear()
    sections.clear()
    lines.clear()
    assert hierarchy == HIERARCHY
    for value, field in (
        (hierarchy, "plants"),
        (SECTION, "section_name"),
        (LINE, "line_name"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, "changed")
    other = replace(hierarchy, work=replace(WORK, project_id="other"))
    place = hierarchy.work.available_workplaces()[0]
    assert hierarchy.work.worker_context("w", place) != other.work.worker_context(
        "w", place
    )
