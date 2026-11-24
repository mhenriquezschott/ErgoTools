"""M06 personal settings isolation and complete native demonstration contracts."""

from dataclasses import replace
from pathlib import Path

import pytest
from assessment_contexts import read_contexts
from assessment_tasks import persist_source, preview
from demo_project import build_demo
from mobile_preferences import KINDS, PreferenceStore, TabletPreferences
from project_session import ProjectSession

from ergotools.domain.assessments.document import AssessmentKind


@pytest.mark.parametrize(
    "field,value",
    [
        ("tick_interval", True),
        ("tick_interval", 7),
        ("animation_ms", 99),
        ("animation_ms", 1001),
        ("range_labels", 1),
        ("task_names", (True, False)),
        ("task_details", (True, 1, False)),
    ],
)
def test_invalid_preferences_rejected(field: str, value: object) -> None:
    """Refuse coerced/unsupported values rather than changing presentation silently.

    Args:
        field: Configuration field under validation.
        value: Invalid boundary/type example.

    Returns:
        None; no persistent/native data is involved.
    """
    with pytest.raises(ValueError):
        replace(TabletPreferences(), **{field: value})


def test_preferences_persist_separately_and_bad_file_survives(tmp_path: Path) -> None:
    """Apply survives restart without native history/dirty/bytes changes.

    Args:
        tmp_path: Private app storage.

    Returns:
        None; malformed JSON retains evidence and safely restores defaults.
    """
    session = ProjectSession(tmp_path)
    session.create("Settings isolation")
    before = (
        session.working.read_bytes(),
        session.active.copy(),
        session.history.undo_label_key,
    )
    store = PreferenceStore(tmp_path)
    assert store.load() == TabletPreferences()
    desired = replace(
        TabletPreferences(),
        tick_interval=20,
        task_names=(False, True, False),
        damage_animation=False,
    )
    store.save(desired)
    assert PreferenceStore(tmp_path).load() == desired
    assert [desired.names_for(k) for k in KINDS] == [False, True, False]
    assert all(desired.details_for(k) for k in KINDS)
    assert (
        session.working.read_bytes(),
        session.active,
        session.history.undo_label_key,
    ) == before
    store.path.write_text("{broken")
    assert store.load() == TabletPreferences() and store.warning
    assert store.path.read_text() == "{broken"


def test_complete_demo_real_results_and_private_roundtrip(tmp_path: Path) -> None:
    """All tools/owners remain portable; copying the prepared example is independent.

    Args:
        tmp_path: Dedicated disposable project destinations.

    Returns:
        None; actual result precision agrees with unchanged core evaluation.
    """
    path = tmp_path / "demo.ergprj"
    build_demo(path)
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        build_demo(path)
    assert path.read_bytes() == original
    records = read_contexts(path)["records"]
    assert len(records) == 19
    assert len({r["worker"].worker_id for r in records}) == 4
    assert sum(r["result"] is not None for r in records) == 18
    assert sum(not r["active"] for r in records) == 1
    assert {r["owner"].kind for r in records} == set(AssessmentKind)
    assert {r["job"] for r in records} == {
        "No Job assigned",
        "J01 · Manual packing",
        "J02 · Container transfer",
    }
    for r in records:
        calculated = preview(r["document"], r["source"], r["units"])["result"]
        assert calculated == r["result"]
    session = ProjectSession(tmp_path / "private")
    session.activate(original, "Prepared sample", "Fictional complete demo")
    selected = next(
        r
        for r in read_contexts(session.working)["records"]
        if r["owner"].kind is AssessmentKind.LIFFT
    )
    source = selected["source"]
    session.change(
        "Edit",
        lambda: persist_source(
            session.working,
            selected,
            replace(source, tasks=(replace(source.tasks[0], repetitions=200),)),
        ),
    )
    assert session.working.read_bytes() != original and path.read_bytes() == original
    session.replay()
    assert session.working.read_bytes() == original
    session.save()
    session.open_recent(session.active["id"])
    assert len(read_contexts(session.working)["records"]) == 19
