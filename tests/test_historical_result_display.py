"""Saved palette continuity must not overwrite original archived evidence.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

from dataclasses import replace

import pytest

from ergotools.application.assessments.evaluation import EvaluationStatus
from ergotools.application.historical_results import (
    HistoricalAssessmentResult,
    HistoricalTaskResult,
)
from ergotools.domain.assessments.document import AssessmentDraft
from ergotools.presentation.desktop.historical_result_display import (
    historical_damage_color,
)
from ergotools.presentation.desktop.theme.duet_colors import duet_damage_color
from ergotools.presentation.desktop.theme.lifft_colors import lifft_damage_color
from ergotools.presentation.desktop.theme.tst_colors import tst_damage_color
from tests.test_saved_results import SOURCES


@pytest.mark.parametrize("source", SOURCES)
def test_fresh_saved_color_retains_row_precision(source: AssessmentDraft) -> None:
    """Rounded summaries keep fresh colors; archives keep recorded-summary colors.

    Args:
        source: Immutable draft or disposable source path supplied by the stated
            storage/publication scenario.

    Returns:
        None.
    """
    from ergotools.domain.assessments.document import AssessmentKind, assessment_kind

    palette, damage = {
        AssessmentKind.LIFFT: (lifft_damage_color, 0.00005),
        AssessmentKind.DUET: (duet_damage_color, 0.00002),
        AssessmentKind.TST: (tst_damage_color, 0.00002),
    }[assessment_kind(source)]
    recorded = round(damage, 4)
    result = HistoricalAssessmentResult(
        source,
        recorded,
        0.0,
        (HistoricalTaskResult(None, damage / 2, 50.0),) * 2,
        calculation_status=EvaluationStatus.COMPLETE,
    )
    assert palette(damage) != palette(recorded)
    assert historical_damage_color(result) == palette(damage)
    assert result.damage == recorded and result.source is source
    archived = replace(result, calculation_status=None)
    assert historical_damage_color(archived) == palette(recorded)


def test_absent_rows_and_zero_fresh_damage() -> None:
    """Absent evidence falls back to the summary; zero fresh output stays clear.

    Args:
        None.

    Returns:
        None.
    """
    result = HistoricalAssessmentResult(
        SOURCES[0],
        0.2,
        0.0,
        (),
        calculation_status=EvaluationStatus.PARTIAL,
    )
    assert historical_damage_color(result) == lifft_damage_color(0.2)
    missing = replace(result, tasks=(HistoricalTaskResult(None, None, None),))
    assert historical_damage_color(missing) == lifft_damage_color(0.2)
    zero = replace(result, damage=0.0, tasks=(HistoricalTaskResult(None, 0.0, None),))
    assert historical_damage_color(zero) is None
    assert historical_damage_color(
        replace(zero, calculation_status=None)
    ) == lifft_damage_color(0.0)
    assert historical_damage_color(replace(result, damage=None)) is None
