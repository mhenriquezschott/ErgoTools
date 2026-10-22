"""Reference ownership constraints and historical assignment isolation.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace
from datetime import date

import pytest

from ergotools.application.job_classification import (
    ClassificationRequest,
    classify_assignments,
)
from ergotools.domain.assessment_history import (
    AssessmentHistory,
    AssignmentAssessment,
)
from ergotools.domain.assessments.context import WorkerContext
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.job_catalog import (
    Job,
    JobCatalog,
    JobPlacement,
    WorkerJobAssignment,
)
from ergotools.domain.work_catalog import StationKey

# Synthetic LiFFT ownership record; rejection cases add a conflicting document
# or assignment/tool owner against it.
RECORD = AssignmentAssessment("a", 1, AssessmentKind.LIFFT, worker_id="w")


def test_reassignment_never_moves_historical_assessment() -> None:
    """An assessment on a closed row cannot become a successor's current source.

    Args:
        None.

    Returns:
        None.
    """
    place = StationKey("P", "S", "L", "1").at_shift("Day")
    owner = WorkerContext("p", "w", place)
    jobs = JobCatalog(
        "p",
        (Job("j", "Job"),),
        (JobPlacement(1, "j", place),),
        (WorkerJobAssignment(1, owner, 1),),
    )
    history = AssessmentHistory("p", (RECORD,))
    successor = classify_assignments(
        jobs,
        "w",
        (ClassificationRequest(1, None, 2),),
        effective_date=date(2026, 10, 1),
    )
    history.validate_jobs(successor)
    assert history.current_for(1, AssessmentKind.LIFFT) is RECORD
    assert history.current_for(2, AssessmentKind.LIFFT) is None
    new = AssignmentAssessment("b", 2, AssessmentKind.LIFFT, worker_id="w")
    both = replace(history, entries=(RECORD, new))
    both.validate_jobs(successor)
    assert both.current_for(2, AssessmentKind.LIFFT) is new
    assert both.current_for(1, AssessmentKind.DUET) is None
    with pytest.raises(ValueError):
        history.validate_jobs(
            replace(successor, assignments=(successor.assignments[1],))
        )
    with pytest.raises(ValueError):
        history.validate_jobs(JobCatalog("other"))


def test_invalid_typed_ownership_and_duplicate_documents() -> None:
    """Reject booleans as integers, invalid tool identities and copied documents.

    Args:
        None.

    Returns:
        None.
    """
    for changes in (
        {"document_id": ""},
        {"assignment_id": True},
        {"kind": "lifft"},
    ):
        with pytest.raises(ValueError):
            replace(RECORD, **changes)
    with pytest.raises(ValueError):
        AssessmentHistory("p", (None,))
    with pytest.raises(ValueError):
        AssessmentHistory("p", (RECORD, replace(RECORD, assignment_id=2)))
    history = AssessmentHistory("p")
    for identity, kind in ((True, AssessmentKind.LIFFT), (1, "lifft")):
        with pytest.raises(ValueError):
            history.current_for(identity, kind)
    assert history.current_for(1, AssessmentKind.LIFFT) is None
