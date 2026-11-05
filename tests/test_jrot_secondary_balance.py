"""Independent secondary-objective oracle and native restriction bulk-action checks.

All catalogs/projects are disposable. Enumeration uses rational score arithmetic,
not a second implementation of the linear model or its termination status.
"""

from itertools import combinations
from pathlib import Path

import pytest
from PyQt5.QtTest import QTest

from ergotools.bootstrap import load_icons
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.language import Language
from ergotools.infrastructure.highs_rotation_optimizer import HighsRotationPlanner
from ergotools.presentation.desktop.jrot_rules_dialog import JrotRulesDialog
from tests.test_jrot_guided_ui import dispose
from tests.test_jrot_planning_ui import planning_dialog
from tests.test_rotation_planning import enumerate_scores, planning


@pytest.mark.parametrize(
    "tools", [tuple(c) for n in (1, 2, 3) for c in combinations(AssessmentKind, n)]
)
def test_every_subset_preserves_minimax_then_minimizes_spread(
    tools: tuple[AssessmentKind, ...],
) -> None:
    """Compare both objectives with exhaustive small unequal-block schedules.

    Args:
        tools: All seven nonempty tool subsets, exercising direct HiGHS.

    Returns:
        None; first-stage best value and the best compatible spread match the oracle.
    """
    vectors = {
        AssessmentKind.LIFFT: (0, 25, 55),
        AssessmentKind.DUET: (5, 30, 60),
        AssessmentKind.TST: (10, 30, 54),
    }
    problem = planning(tuple(vectors[k] for k in tools), (30, 30, 180), tools)
    oracle = enumerate_scores(problem)
    optimum = min(sum(max(s) for s in candidate) for candidate in oracle)
    result = HighsRotationPlanner().solve(problem)
    actual = tuple(problem.scores(result.schedule, kind) for kind in tools)
    assert len(result.stages) == 2
    assert sum(max(s) for s in actual) == pytest.approx(float(optimum), abs=0.0004)
    compatible = [
        candidate
        for candidate in oracle
        if all(
            float(max(scores)) <= max(values) + 0.0002
            for scores, values in zip(candidate, actual, strict=True)
        )
    ]
    assert sum(max(s) - min(s) for s in actual) == pytest.approx(
        float(min(sum(max(s) - min(s) for s in c) for c in compatible)), abs=0.0004
    )


@pytest.mark.parametrize("language", list(Language))
def test_bulk_restrictions_are_eligible_local_and_cancellable(
    tmp_path: Path,
    language: Language,
) -> None:
    """Exercise actual header buttons, visible exclusions and unchanged cancellation.

    Args:
        tmp_path: Private project with real native history ownership.
        language: Both maintained caption languages.

    Returns:
        None; complete icon/caption rows fit above bulk actions in both languages;
        bulk prerequisite logic works and cancelling never changes the project.
    """
    root = planning_dialog(tmp_path, language)
    before = root.current()
    dialog = JrotRulesDialog(
        before.inputs,
        {t.key: t.job_id for t in before.inputs.targets},
        load_icons(),
        language,
        root,
    )
    try:
        dialog.show()
        QTest.qWait(20)
        assert dialog.column_header.height() == 68
        assert all(
            host.y() > dialog.column_header.fontMetrics().height() + 12
            for host in dialog.column_header.hosts.values()
        )
        for width in (1240, 1100):
            dialog.resize(width, 620)
            QTest.qWait(20)
            for column in range(6):
                item = dialog.table.horizontalHeaderItem(column)
                assert item is not None and not item.icon().isNull()
                assert dialog.table.columnWidth(column) >= (
                    dialog.column_header.fontMetrics().horizontalAdvance(item.text())
                    + dialog.column_header.iconSize().width()
                    + 24
                )
            for column, host in dialog.column_header.hosts.items():
                assert host.width() >= host.sizeHint().width()
                assert host.geometry().bottom() < dialog.column_header.height()
                assert host.x() == (
                    dialog.column_header.sectionViewportPosition(column) + 1
                )
        buttons = dialog.column_header.buttons
        assert not buttons[4][0].isEnabled()
        buttons[3][0].click()
        assert all(c[2].isChecked() for c in dialog.controls.values())
        buttons[4][0].click()
        buttons[5][0].click()
        assert all(
            c[3].isChecked() and c[4].isChecked() for c in dialog.controls.values()
        )
        buttons[3][1].click()
        assert all(
            not any(c[i].isChecked() for i in (2, 3, 4))
            for c in dialog.controls.values()
        )
        worker = next(iter(dialog.controls))
        key = before.inputs.targets[0].key
        dialog.excluded[worker] = {key}
        dialog.update_exclusion_label(worker)
        assert (
            before.inputs.targets[0].job_id in dialog.exclusion_summaries[worker].text()
        )
        buttons[2][0].click()
        assert not any(dialog.excluded.values())
        dialog.reject()
        assert root.current() == before
    finally:
        dialog.deleteLater()
        dispose(root)
