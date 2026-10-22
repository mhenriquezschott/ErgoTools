"""Frozen reference catalogs, exact ownership validation and source immutability.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.work_catalog import StationKey, WorkCatalog, WorkerEntry
from ergotools.presentation.worker_options import WorkerOrder, worker_options

# Exact synthetic station ancestry; repeated station captions on other branches remain
# distinct.
STATION = StationKey("P", "S", "L", "001")
# Immutable synthetic worker identity/details used to characterize catalog labels or
# exact ownership.
WORKER = WorkerEntry("worker id", "First", "Last")
# Immutable exact synthetic worker/job/catalog relationships used by these isolated
# regressions.
CATALOG = WorkCatalog("project", (WORKER,), (STATION,), ("Day", "Night"))


def test_reference_catalogs_and_worker_labels() -> None:
    """Replay actual reference methods without depending on the original checkout.

    Args:
        None.

    Returns:
        None.
    """
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/work_catalog_reference.json").read_text()
    )
    for case in fixture["cases"]:
        catalog = WorkCatalog(
            "project",
            tuple(WorkerEntry(*row) for row in case["workers"]),
            tuple(StationKey(*row) for row in case["stations"]),
            tuple(case["shifts"]),
        )
        assert catalog.available_workplaces() == tuple(
            WorkplaceContext(*row) for row in case["expected_workplaces"]
        ), case["name"]
        for index, order in enumerate((WorkerOrder.ID, WorkerOrder.LAST_NAME)):
            options = worker_options(catalog, order)
            assert [option.label for option in options] == case[
                "expected_worker_labels"
            ][index]
            assert [option.worker_id for option in options] == case[
                "expected_worker_ids"
            ][index]


def test_membership_keeps_project_worker_and_ancestry_identity() -> None:
    """No assignments are needed; each exact worker/station/shift must exist.

    Args:
        None.

    Returns:
        None.
    """
    workplace = STATION.at_shift("Day")
    owner = CATALOG.worker_context(WORKER.worker_id, workplace)
    assert owner.project_id == "project"
    assert owner.worker_id == "worker id"
    assert owner.workplace == workplace
    with pytest.raises(KeyError):
        CATALOG.worker_context("worker", workplace)
    for field in ("plant_name", "section_name", "line_name", "station_id", "shift_id"):
        with pytest.raises(KeyError):
            CATALOG.worker_context(
                WORKER.worker_id, replace(workplace, **{field: "other"})
            )
    other = replace(CATALOG, project_id="other")
    assert other.worker_context(WORKER.worker_id, workplace) != owner


def test_duplicate_keys_fail_but_reused_station_names_are_valid() -> None:
    """Fail conflicting records instead of discarding them through deduplication.

    Args:
        None.

    Returns:
        None.
    """
    for changes in (
        {"workers": (WORKER, replace(WORKER, first_name="Different"))},
        {"stations": (STATION, STATION)},
        {"shifts": ("Day", "Day")},
    ):
        with pytest.raises(ValueError, match="unique"):
            replace(CATALOG, **changes)
    catalog = replace(CATALOG, stations=(STATION, replace(STATION, plant_name="Other")))
    assert len(catalog.available_workplaces()) == 4
    assert len(set(catalog.available_workplaces())) == 4


def test_snapshot_copies_collections_and_values_are_frozen() -> None:
    """Caller mutations cannot alter an already published selection snapshot.

    Args:
        None.

    Returns:
        None.
    """
    workers, stations, shifts = [WORKER], [STATION], ["Day"]
    catalog = WorkCatalog("project", workers, stations, shifts)
    workers.clear()
    stations.clear()
    shifts.append("Night")
    assert catalog.available_workplaces() == (STATION.at_shift("Day"),)
    assert catalog.workers == (WORKER,)
    for value, field in (
        (catalog, "project_id"),
        (WORKER, "worker_id"),
        (STATION, "station_id"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field, "changed")


@pytest.mark.parametrize("invalid", ["", " \t", None, 1, True])
def test_invalid_identifiers_are_not_coerced(invalid: object) -> None:
    """Reject incomplete catalog identity while allowing empty optional names.

    Args:
        invalid: Deliberately invalid typed boundary value; must fail without partial
            state changes.

    Returns:
        None.
    """
    with pytest.raises(ValueError):
        replace(WORKER, worker_id=invalid)
    with pytest.raises(ValueError):
        replace(CATALOG, project_id=invalid)
    with pytest.raises(ValueError):
        replace(CATALOG, shifts=(invalid,))
    for field in ("plant_name", "section_name", "line_name", "station_id"):
        with pytest.raises(ValueError):
            replace(STATION, **{field: invalid})


def test_untyped_records_and_names_are_rejected() -> None:
    """Require explicit catalog objects and optional text, not inferred row shapes.

    Args:
        None.

    Returns:
        None.
    """
    for field in ("first_name", "last_name"):
        for invalid in (1, True, []):
            with pytest.raises(ValueError, match="names"):
                replace(WORKER, **{field: invalid})
    for field in ("workers", "stations"):
        with pytest.raises(ValueError, match="typed"):
            replace(CATALOG, **{field: (None,)})
    with pytest.raises(ValueError, match="ordering"):
        worker_options(CATALOG, "id")


def test_options_keep_ids_separate_and_stable_ties() -> None:
    """Whitespace IDs and equal surnames need no label parsing or fabricated IDs.

    Args:
        None.

    Returns:
        None.
    """
    second = WorkerEntry("001", "Other", "Last")
    catalog = replace(CATALOG, workers=(WORKER, second))
    options = worker_options(catalog, WorkerOrder.LAST_NAME)
    assert [option.worker_id for option in options] == ["worker id", "001"]
    assert options[0].label == "worker id (Last, First)"
    assert worker_options(replace(catalog, workers=()), WorkerOrder.ID) == ()
    assert (
        replace(catalog, workers=()).available_workplaces()
        == CATALOG.available_workplaces()
    )
