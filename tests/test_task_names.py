"""Named-task source, catalog and migration regressions without operational writes.

Test layer. Synthetic sources use established calculator conventions and disposable
native files. Reusable labels cannot alias numeric inputs/results; private migrations
must retain every existing table value and source/result binding exactly.
"""

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

import pytest

from ergotools.application.job_calculation import (
    blank_job_source,
    calculate_job_measurement,
)
from ergotools.application.session import DocumentKey
from ergotools.application.task_catalog import label_assessment_task
from ergotools.domain.assessments.document import (
    AssessmentKind,
    task_has_content,
    task_has_data,
)
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.model_units import MeasurementSystem
from ergotools.domain.project import ProjectMetadata
from ergotools.domain.task_catalog import TaskDefinition
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.assessment_serialization import (
    decode_assessment,
    encode_assessment,
)
from tools.project_migration.ergotools_migration.previous_project import (
    upgrade_previous_project,
)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_named_codec_roundtrip_and_independent_calculations(
    kind: AssessmentKind,
) -> None:
    """Keep names/IDs exactly while calculator results depend only on measurements.

    Args:
        kind: All three established tool source models, including ST conventions.

    Returns:
        None; roundtrip/rename/copy assertions use full-precision source quantities.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    if isinstance(source, DuetDraft):
        source = replace(
            source, tasks=(replace(source.tasks[0], omni_res_scale=4, repetitions=100),)
        )
    elif isinstance(source, LifftDraft):
        source = replace(
            source,
            tasks=(
                replace(
                    source.tasks[0], lever_arm=30.123456789, load=49.05, repetitions=100
                ),
            ),
        )
    else:
        source = replace(
            source,
            tasks=(
                replace(
                    source.tasks[0], lever_arm=30.123456789, load=49.05, repetitions=100
                ),
            ),
        )
    original_payload = encode_assessment(source)
    named = label_assessment_task(
        source, source.tasks[0].task_id, "Corte / trimming ñ", "task-cut"
    )
    assert decode_assessment(encode_assessment(named)) == named
    expected = calculate_job_measurement("p", "j", source, MeasurementSystem.METRIC)
    actual = calculate_job_measurement("p", "j", named, MeasurementSystem.METRIC)
    assert actual.cumulative_damage == expected.cumulative_damage
    assert actual.probability_percent == expected.probability_percent
    assert actual.task_results == expected.task_results
    renamed = label_assessment_task(
        named, named.tasks[0].task_id, "Local variation", None
    )
    assert renamed.tasks[0].task_definition_id is None
    assert source.tasks[0].task_name is None
    assert encode_assessment(source) == original_payload


@pytest.mark.parametrize(
    "name,identity", [("", None), (12, None), ("Cutting", ""), (None, "task")]
)
def test_invalid_name_metadata_rejects_before_source_write(
    name: str | None, identity: str | None
) -> None:
    """Malformed optional metadata never becomes a calculator input or a dangling label.

    Args:
        name: Explicit invalid type/blank/missing label case.
        identity: Definition reference requiring a nonblank fallback name.

    Returns:
        None; constructor rejects invalid metadata before any database is opened.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    with pytest.raises(ValueError):
        label_assessment_task(source, source.tasks[0].task_id, name, identity)


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_name_only_row_is_preserved_but_not_calculated(kind: AssessmentKind) -> None:
    """Names require deletion consent but do not fabricate complete numeric tasks.

    Args:
        kind: Tool whose default selector alone is not substantive measurement data.

    Returns:
        None; calculation and destructive-operation predicates remain distinct.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    named = label_assessment_task(source, source.tasks[0].task_id, "Pressing", None)
    assert task_has_content(named.tasks[0])
    assert not task_has_data(named.tasks[0])
    assert decode_assessment(encode_assessment(named)) == named


def test_catalog_rename_preserves_source_bytes_and_referenced_delete_rolls_back(
    tmp_path: Path,
) -> None:
    """Reusable name edits do not rewrite measured sources or merge equal-name IDs.

    Args:
        tmp_path: Disposable project directory; maintained fixtures remain untouched.

    Returns:
        None; exact source bytes, reference protection and reopen integrity are checked.
    """
    path = tmp_path / "named.ergprj"
    metadata = ProjectMetadata("p", "Names", MeasurementSystem.METRIC)
    with AssessmentProjectFile.create_empty(path, metadata) as project:
        assert project.format_version == 24
        a = TaskDefinition("a", "Cutting")
        b = TaskDefinition("b", "Cutting")
        project.replace_task_definitions((), (a, b))
        source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
        named = label_assessment_task(
            source, source.tasks[0].task_id, a.name, a.definition_id
        )
        key = DocumentKey("p", "source")
        project.save(key, named)
        before = project._connection.execute(
            "SELECT payload FROM draft_documents"
        ).fetchone()
        renamed = replace(a, name="Cutting thin material")
        project.replace_task_definitions((a, b), (renamed, b))
        assert (
            project._connection.execute(
                "SELECT payload FROM draft_documents"
            ).fetchone()
            == before
        )
        assert project.load(key) == named
        with pytest.raises(ValueError, match="referenced"):
            project.replace_task_definitions((renamed, b), (b,))
        assert project.load_task_definitions() == (renamed, b)
        with pytest.raises(ValueError, match="stale"):
            project.replace_task_definitions((a, b), (a,))
        invalid = label_assessment_task(
            named, named.tasks[0].task_id, "Foreign", "elsewhere"
        )
        with pytest.raises(ValueError, match="unknown"):
            project.save(key, invalid)
        assert project.load(key) == named
    with AssessmentProjectFile.open(path) as reopened:
        assert reopened.load_task_definitions()[0].name == renamed.name
        assert reopened.load(key) == named


def test_upgrade19_adds_only_empty_catalog_and_format_marker(tmp_path: Path) -> None:
    """External migration retains exact table rows without editing its source.

    Args:
        tmp_path: Private native source/destination directory, not an operational file.

    Returns:
        None; table values and bytes prove preservation across the private upgrade.
    """
    old = tmp_path / "old.ergprj"
    new = tmp_path / "new.ergprj"
    metadata = ProjectMetadata("p", "Migration", MeasurementSystem.METRIC)
    with AssessmentProjectFile._create(old, metadata, version=19) as previous:
        source = blank_job_source(AssessmentKind.DUET, MeasurementSystem.METRIC)
        previous.save(DocumentKey("p", "source"), source)
    original = old.read_bytes()
    with upgrade_previous_project(old, new) as upgraded:
        assert upgraded.format_version == 24
        assert upgraded.load_task_definitions() == ()
        assert upgraded.load(DocumentKey("p", "source")) == source
    assert old.read_bytes() == original
    with closing(sqlite3.connect(old)) as a, closing(sqlite3.connect(new)) as b:
        tables = [
            row[0]
            for row in a.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
        for table in tables:
            if table == "project_metadata":
                assert (
                    a.execute(
                        "SELECT format,project_id,title,default_units "
                        "FROM project_metadata"
                    ).fetchall()
                    == b.execute(
                        "SELECT format,project_id,title,default_units "
                        "FROM project_metadata"
                    ).fetchall()
                )
            else:
                assert (
                    a.execute(f'SELECT * FROM "{table}"').fetchall()
                    == b.execute(f'SELECT * FROM "{table}"').fetchall()
                ), table


@pytest.mark.parametrize("identity", [None, "", 3, True])
def test_definition_requires_a_real_identity(identity: str) -> None:
    """Require definition identities even though source-row references are optional.

    Args:
        identity: Explicit invalid/missing definition identity.

    Returns:
        None; invalid entries fail before SQLite text affinity can coerce them.
    """
    with pytest.raises(ValueError):
        TaskDefinition(identity, "Cutting")


@pytest.mark.parametrize("kind", list(AssessmentKind))
@pytest.mark.parametrize("move", [False, True])
def test_named_copy_move_preserves_catalog_result_and_shared_history(
    tmp_path: Path, kind: AssessmentKind, move: bool
) -> None:
    """Transfer named measured rows exactly, with one reversible transaction.

    Args:
        tmp_path: Disposable native project directory; maintained projects stay closed.
        kind: Each calculator, including ST's recorded direction convention.
        move: Remove only the source when True; otherwise retain independent copies.

    Returns:
        None; exact labels, references, results, catalog, Undo/Redo and reopen hold.
    """
    from ergotools.application.document_lifecycle import CloseChoice
    from ergotools.application.job_calculation import copy_job_tasks
    from ergotools.domain.assessment_transfer import TransferRequest
    from tests.test_workplace_assignment_workflow import (
        STATION,
        open_private,
        seed_workplace_source,
    )

    path = seed_workplace_source(tmp_path, kind)
    definition = TaskDefinition("packing", "Packing cartons")
    with AssessmentProjectFile.open(path) as project:
        project.replace_task_definitions((), (definition,))
        key = project.list_assessments()[0].document
        saved = project.load_saved_result(key)
        assert saved is not None
        source = label_assessment_task(
            saved.source,
            saved.source.tasks[0].task_id,
            definition.name,
            definition.definition_id,
        )
        saved = replace(saved, source=source)
        project.save_result(key, saved)
    workspace = open_private(path)
    try:
        owner = workspace.read_hierarchy().hierarchy.work.worker_context(
            "A", STATION.at_shift("1")
        )
        request = TransferRequest(None, owner, (kind,), move, "A")
        assert workspace.transfer_assessments(
            workspace.read_jobs(), workspace.read_history(), request, {kind: "copy"}
        ).completed
        assert workspace.saved_assessment_result("copy") == saved
        assert workspace.load_task_definitions() == (definition,)
        assert workspace.editing.replay(redo=False)
        assert workspace.read_history().history.current_for(1, kind) is None
        assert workspace.editing.replay(redo=True)
        assert workspace.save()
        with AssessmentProjectFile.open(path) as project:
            copied_key = next(
                entry.document
                for entry in project.list_assessments()
                if entry.document.document_id == "copy"
            )
            assert project.load(copied_key) == source
            assert project.load_saved_result(copied_key) == saved
        measurement = calculate_job_measurement(
            "p", "job", source, MeasurementSystem.METRIC
        )
        copied = copy_job_tasks(
            measurement,
            (source.tasks[0].task_id,),
            project_id="p",
            units=MeasurementSystem.METRIC,
        )
        assert copied.source.tasks[0] == source.tasks[0]
    finally:
        workspace.close(choice=CloseChoice.DISCARD)
