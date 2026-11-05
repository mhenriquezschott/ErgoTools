"""Atomic named-task clipboard parsing, units, precision and missing-value contracts.

Test layer. Plain TSV values never execute spreadsheet formulas. Exact source snapshots
prove failed batches have no effects; current calculator conventions remain unchanged.
"""

from dataclasses import replace

import pytest

from ergotools.application.assessment_clipboard import (
    assessment_clipboard_text,
    assessment_input_fields,
    clipboard_rows,
    prepare_assessment_paste,
)
from ergotools.application.job_calculation import blank_job_source
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.assessments.duet_draft import DuetDraft
from ergotools.domain.assessments.lifft_draft import LifftDraft
from ergotools.domain.assessments.tst import TstDirection
from ergotools.domain.assessments.tst_draft import TstDraft
from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.model_units import MeasurementSystem


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_two_rows_are_one_prepared_source_with_stable_existing_identity(
    kind: AssessmentKind,
) -> None:
    """Mapped name/inputs expand a grid without changing its tool/units/retained ID.

    Args:
        kind: Each assessment schema and selector format.

    Returns:
        None; original snapshots remain unchanged after valid batch preparation.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    fields = assessment_input_fields(source)
    rows = (
        (("Trimming", "2: Easy", "100"), ("Pressing", "4", "200"))
        if isinstance(source, DuetDraft)
        else (
            (
                ("Trimming", "Handling Load", "30.123456789", "49.05", "100"),
                ("Pressing", "Horizontal Push/Pull", "20", "10", "200"),
            )
            if isinstance(source, TstDraft)
            else (
                ("Trimming", "30.123456789", "49.05", "100"),
                ("Pressing", "20", "10", "200"),
            )
        )
    )
    result = prepare_assessment_paste(source, rows, fields)
    assert result.tasks[0].task_id == source.tasks[0].task_id
    assert len(result.tasks) == 2
    assert result.tasks[0].task_name == "Trimming"
    assert result.tasks[1].task_name == "Pressing"
    assert result.tasks[1].repetitions == 200
    assert len(source.tasks) == 1 and source.tasks[0].repetitions is None
    assert result.tasks[0].task_definition_id is None
    if isinstance(result, TstDraft):
        assert result.tasks[1].direction is TstDirection.HORIZONTAL
        assert result.direction_convention is source.direction_convention


@pytest.mark.parametrize("token", ["NaN", "inf", "=A1", "bad", "1,000", "-1", "1e999"])
def test_invalid_last_cell_rejects_entire_batch(token: str) -> None:
    """Earlier valid rows never leak from a partially parsed clipboard batch.

    Args:
        token: Nonfinite, formula, malformed, grouped, negative or overflow token.

    Returns:
        None; original source remains exact and no replacement is returned.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    with pytest.raises((ValueError, DraftError)):
        prepare_assessment_paste(
            source,
            (("A", "30", "49", "100"), ("B", "20", token, "2")),
            assessment_input_fields(source),
        )
    assert len(source.tasks) == 1
    assert source.tasks[0].task_name is None and source.tasks[0].load is None


def test_comma_precision_unit_conversion_and_unchanged_roundtrip() -> None:
    """Pasted inputs use the existing decimal/force policy without display rounding.

    Args:
        None.

    Returns:
        None; same projected values preserve the exact canonical numeric tokens.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.IMPERIAL)
    assert isinstance(source, LifftDraft)
    source = replace(
        source,
        tasks=(
            replace(
                source.tasks[0],
                task_name="  Trimming / corte  ",
                lever_arm=12.123456789123,
                load=10.987654321987,
                repetitions=123,
            ),
        ),
    )
    text = assessment_clipboard_text(
        source, (), DecimalConvention.COMMA, MeasurementSystem.METRIC
    )
    rows = clipboard_rows(text)
    copied = prepare_assessment_paste(
        source,
        rows[1:],
        assessment_input_fields(source),
        convention=DecimalConvention.COMMA,
        input_system=MeasurementSystem.METRIC,
    )
    assert copied == source
    assert "(cm)" in rows[0][1] and "(N)" in rows[0][2]
    blanked = prepare_assessment_paste(source, (("",),), ("load",))
    assert blanked.tasks[0].load is None
    assert blanked.tasks[0].lever_arm == source.tasks[0].lever_arm


@pytest.mark.parametrize("fields", [("load", "load"), ("task_id", None), (None, None)])
def test_invalid_mapping_is_rejected(fields: tuple[str | None, ...]) -> None:
    """Duplicate targets, identity writes and all-ignored mappings cannot paste.

    Args:
        fields: Explicit invalid mapping with the same number of source cells.

    Returns:
        None; validated source stays unchanged.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    with pytest.raises(ValueError, match="mapping"):
        prepare_assessment_paste(source, (("1", "2"),), fields)


def test_clipboard_shape_capacity_and_quoted_names() -> None:
    """TSV quoting preserves literal names; inconsistent rows and oversized grids fail.

    Args:
        None.

    Returns:
        None; exactly 100 tasks is allowed, 101 data rows is rejected before acceptance.
    """
    assert clipboard_rows('"Cut\ttrim"\t30\r\n') == (("Cut\ttrim", "30"),)
    for text in ("", "a\tb\nc", '"unclosed'):
        with pytest.raises(ValueError):
            clipboard_rows(text)
    source = blank_job_source(AssessmentKind.DUET, MeasurementSystem.METRIC)
    full = prepare_assessment_paste(
        source, tuple((str(i),) for i in range(100)), ("task_name",)
    )
    assert len(full.tasks) == 100
    with pytest.raises(ValueError):
        prepare_assessment_paste(
            source, tuple((str(i),) for i in range(101)), ("task_name",)
        )
