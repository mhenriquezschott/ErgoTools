"""Worker-owned assessment source selection and compatibility one-task adapter.

M04 supports all worker tool sources in their original units/convention.
The old accept_inputs boundary remains for feasibility/M01 regression callers.
"""

from dataclasses import replace
from pathlib import Path

from assessment_contexts import read_contexts

from ergotools.application.assessments.evaluation import AssessmentEvaluator
from ergotools.application.saved_results import result_snapshot
from ergotools.application.session import DocumentSession
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def assessment(
    path: Path,
    worker_id: str | None = None,
    document_id: str | None = None,
    kind: AssessmentKind = AssessmentKind.LIFFT,
) -> dict | None:
    """Select the first supported worker-owned source without inventing data.

    Args:
        path: Native working copy of any supported current desktop project.
        worker_id: Exact selected worker, or None for the first supported source.
        document_id: Optional existing document to preserve selection through replay.
        kind: Selected tool, with independent ownership and source type.

    Returns:
        Document, source, worker, context and optional saved result, or None.
    """
    records = read_contexts(path)["records"]
    offered = [
        r
        for r in records
        if r["owner"].kind is kind
        and (worker_id is None or r["worker"].worker_id == worker_id)
        and (document_id is None or r["document"].document_id == document_id)
    ]
    return next(
        iter(
            sorted(
                offered,
                key=lambda r: (
                    r["worker"].worker_id.casefold(),
                    r["workplace"] is not None,
                    r["context"].casefold(),
                    r["document"].document_id,
                ),
            )
        ),
        None,
    )


def accept_inputs(
    path: Path, selected: dict, values: list[str], *, calculate: bool
) -> dict:
    """Persist only the selected task to the private workspace, optionally calculate.

    Args:
        path: Active private working file, never the user's external document.
        selected: Exact document/source/owner projection previously loaded.
        values: Lever arm, force and repetitions in source units; blank means absent.
        calculate: Evaluate complete inputs and persist the source-bound result.

    Returns:
        Refreshed selected projection; invalid numeric input preserves the file.
    """
    if len(selected["source"].tasks) != 1:
        raise ValueError("Use the multi-task editor for this assessment.")
    numbers = [float(v) if v.strip() else None for v in values]
    task = replace(
        selected["source"].tasks[0],
        lever_arm=numbers[0],
        load=numbers[1],
        repetitions=numbers[2],
    )
    draft = replace(selected["source"], tasks=(task,))
    result = None
    if calculate:
        result = result_snapshot(
            AssessmentEvaluator().evaluate(
                DocumentSession(selected["document"], draft)
            ),
            draft.system,
        )
        if result is None:
            raise ValueError(
                "Complete all three inputs with valid values before calculating."
            )
    with AssessmentProjectFile.open(path) as project:
        project.begin_editing(lambda label: None)
        if calculate:
            project.save_result(selected["document"], result)
        else:
            project.save(selected["document"], draft)
        project.commit_editing()
    return {**selected, "source": draft, "result": result}
