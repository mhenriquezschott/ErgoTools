"""Tabular imports preserve source values, units, missing data and atomic validation.

Pure mapper and real file-adapter tests use generated private files, not maintained
projects. No workbook formulas are evaluated, no source file is modified and preferences
never contain imported rows/ranges/file paths.
"""

from dataclasses import replace
from pathlib import Path

import pytest
from openpyxl import Workbook

from ergotools.application.assessment_clipboard import assessment_input_fields
from ergotools.application.assessment_import import (
    ImportProfile,
    parse_import_text,
    prepare_import,
)
from ergotools.application.job_calculation import blank_job_source
from ergotools.application.settings import UserSettings
from ergotools.domain.assessments.document import AssessmentKind
from ergotools.domain.decimal_convention import DecimalConvention
from ergotools.domain.language import Language
from ergotools.domain.model_units import MeasurementSystem
from ergotools.infrastructure.settings_store import (
    JsonSettingsStore,
    SettingsFormatError,
)
from ergotools.infrastructure.tabular_file_reader import SpreadsheetValueReader


@pytest.mark.parametrize("delimiter", ["\t", ",", ";", "|"])
def test_delimited_quotes_and_blank_cells_remain_explicit(delimiter: str) -> None:
    """Quoted names and blank cells keep their exact selected row/column positions.

    Args:
        delimiter: Common source separator, detected or explicitly selected.

    Returns:
        None; newline/diacritic task names and final blank data rows are preserved.
    """
    text = (
        f'"Muñoz{delimiter} revisión"{delimiter}30{delimiter}49.05\n'
        f'"Línea\nNorte"{delimiter}{delimiter}10\n{delimiter}{delimiter}\n'
    )
    rows = parse_import_text(text, delimiter)
    assert rows == (
        (f"Muñoz{delimiter} revisión", "30", "49.05"),
        ("Línea\nNorte", "", "10"),
        ("", "", ""),
    )
    assert parse_import_text(text) == rows


@pytest.mark.parametrize("kind", list(AssessmentKind))
def test_tool_input_import_uses_shared_exact_atomic_preparation(
    kind: AssessmentKind,
) -> None:
    """Every tool keeps input precision, row identity and Unicode names.

    Args:
        kind: LiFFT, DUET or ST input schema.

    Returns:
        None; invalid second rows never mutate the source or partially apply the first.
    """
    source = blank_job_source(kind, MeasurementSystem.METRIC)
    fields = assessment_input_fields(source)
    row = (
        ("Inspección Ñ", "4", "1234")
        if kind is AssessmentKind.DUET
        else (
            ("Inspección Ñ", "Handling Load", "30.123456789", "49.05", "1234")
            if kind is AssessmentKind.TST
            else ("Inspección Ñ", "30.123456789", "49.05", "1234")
        )
    )
    profile = ImportProfile(kind, header=False, fields=fields, configured=True)
    prepared = prepare_import(source, (row, row), profile)
    assert prepared.tasks[0].task_id == source.tasks[0].task_id
    assert prepared.tasks[0].task_name == "Inspección Ñ"
    assert prepared.tasks[1].repetitions == 1234
    assert len(source.tasks) == 1 and source.tasks[0].repetitions is None
    invalid = (*row[:-1], "-10")
    with pytest.raises(ValueError):
        prepare_import(source, (row, invalid), profile)
    assert len(source.tasks) == 1 and source.tasks[0].repetitions is None


@pytest.mark.parametrize(
    "mark,decimal,token",
    [(".", ",", "1.234,5"), (",", ".", "1,234.5"), (" ", ",", "1 234,5")],
)
def test_grouping_is_explicit_and_never_silently_changes_magnitude(
    mark: str, decimal: str, token: str
) -> None:
    """Explicit grouping/decimal choices normalize valid grammar without rounding.

    Args:
        mark: Chosen thousands separator.
        decimal: Independent chosen decimal separator.
        token: Equivalent source numeric representation.

    Returns:
        None; malformed grouping is rejected instead of guessed.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    profile = ImportProfile(
        AssessmentKind.LIFFT,
        header=False,
        fields=("load",),
        decimal=DecimalConvention(decimal),
        thousands=mark,
    )
    result = prepare_import(source, ((token,),), profile)
    assert result.tasks[0].load == 1234.5
    with pytest.raises(ValueError):
        prepare_import(source, (("12" + mark + "34",),), profile)


def test_mapping_capacity_units_and_formula_validation() -> None:
    """Ignore/reorder source columns but never import identities/results or formulas.

    Args:
        None.

    Returns:
        None; impossible mappings, kg units, formula text and oversized batches fail.
    """
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    profile = ImportProfile(
        AssessmentKind.LIFFT, fields=("load", None, "repetitions", "lever_arm")
    )
    rows = (
        ("Load (N)", "Damage", "Repetitions", "Lever arm (cm)"),
        ("49.05", "not an input", "100", "30"),
    )
    result = prepare_import(source, rows, profile)
    assert result.tasks[0].lever_arm == 30 and result.tasks[0].load == 49.05
    for fields in [("damage",), ("task_id",), ("load", "load")]:
        with pytest.raises(ValueError):
            ImportProfile(AssessmentKind.LIFFT, fields=fields)
    with pytest.raises(ValueError):
        prepare_import(
            source, (("Load (kg)",), ("5",)), replace(profile, fields=("load",))
        )
    with pytest.raises(ValueError):
        prepare_import(
            source,
            (("=1+1",),),
            ImportProfile(AssessmentKind.LIFFT, header=False, fields=("load",)),
        )
    with pytest.raises(ValueError):
        prepare_import(
            source,
            tuple(("1",) for _ in range(101)),
            ImportProfile(AssessmentKind.LIFFT, header=False, fields=("load",)),
        )


@pytest.mark.parametrize(
    "encoding", ["utf-8-sig", "utf-16", "cp1252", "iso8859-1", "iso8859-15"]
)
def test_csv_encodings_preserve_spanish_and_european_text(
    tmp_path: Path, encoding: str
) -> None:
    """Explicit common encodings preserve ñ/accents and quoted decimal-comma fields.

    Args:
        tmp_path: Private text-file location.
        encoding: Each offered text encoding.

    Returns:
        None; file bytes remain exact after reading.
    """
    path = tmp_path / "fuente.csv"
    path.write_bytes(
        'Nombre;Brazo;Carga;Repeticiones\n"Muñoz, inspección";30,5;49,05;100\n'.encode(
            encoding
        )
    )
    original = path.read_bytes()
    profile = ImportProfile(AssessmentKind.LIFFT, delimiter=";", encoding=encoding)
    table = SpreadsheetValueReader().read(str(path), profile)
    assert table.rows[1] == ("Muñoz, inspección", "30,5", "49,05", "100")
    assert path.read_bytes() == original and not table.sheets
    if encoding in ("utf-8-sig", "utf-16"):
        assert (
            SpreadsheetValueReader()
            .read(str(path), replace(profile, encoding="auto"))
            .rows
            == table.rows
        )
    else:
        with pytest.raises(ValueError, match="encoding"):
            SpreadsheetValueReader().read(str(path), replace(profile, encoding="auto"))


def test_workbook_sheet_range_selection_and_formula_rejection(tmp_path: Path) -> None:
    """All sheets are selectable and explicit ranges can read beyond initial preview.

    Args:
        tmp_path: Generated private workbook with unrelated notes and distant task rows.

    Returns:
        None; formulas are text, source bytes exact, and only the selected values map.
    """
    path = tmp_path / "workers.xlsx"
    book = Workbook()
    book.active.title = "Información"
    book.active["A1"] = "Notas: no importar"
    page = book.create_sheet("Línea Ñ")
    for column, value in zip(
        "DEFG", ("Task name", "Lever arm (cm)", "Load (N)", "Repetitions"), strict=True
    ):
        page[f"{column}2002"] = value
    for column, value in zip("DEFG", ("Muñoz", 30.5, 49.05, 100), strict=True):
        page[f"{column}2003"] = value
    page["H2003"] = "=SUM(1,2)"
    book.save(path)
    book.close()
    original = path.read_bytes()
    profile = ImportProfile(
        AssessmentKind.LIFFT, fields=("task_name", "lever_arm", "load", "repetitions")
    )
    reader = SpreadsheetValueReader()
    first = reader.read(str(path), profile)
    assert first.sheets == ("Información", "Línea Ñ")
    selected = reader.read(str(path), profile, "Línea Ñ", "D2002:G2003")
    assert selected.sheet == "Línea Ñ" and selected.cell_range == "D2002:G2003"
    source = blank_job_source(AssessmentKind.LIFFT, MeasurementSystem.METRIC)
    assert prepare_import(source, selected.rows, profile).tasks[0].task_name == "Muñoz"
    formula = reader.read(str(path), profile, "Línea Ñ", "H2003:H2003")
    assert formula.rows == (("=SUM(1,2)",),)
    with pytest.raises(ValueError):
        prepare_import(
            source, formula.rows, replace(profile, header=False, fields=("load",))
        )
    for bad_range in ["A:A", "A1:ZZ2001", "A0:B2"]:
        with pytest.raises(ValueError):
            reader.read(str(path), profile, "Línea Ñ", bad_range)
    assert path.read_bytes() == original


def test_application_profiles_roundtrip_without_source_data(tmp_path: Path) -> None:
    """Version-eight settings retain per-tool mappings and reject malformed profiles.

    Args:
        tmp_path: Private settings, never an operational preference file.

    Returns:
        None; unrelated settings survive and preview rows/paths/ranges are not stored.
    """
    path = tmp_path / "settings.json"
    store = JsonSettingsStore(path)
    profile = ImportProfile(
        AssessmentKind.LIFFT,
        fields=("load", None, "lever_arm"),
        delimiter=";",
        encoding="cp1252",
        configured=True,
        headers=("Fuerza", "Nota", "Brazo"),
    )
    settings = replace(UserSettings(), import_profiles=(profile,), undo_limit=12)
    store.save(settings)
    assert store.load() == settings
    assert '"version": 11' in path.read_text()
    assert not any(
        word in path.read_text() for word in ("cell_range", "source_rows", "location")
    )
    import json

    broken = json.loads(path.read_text())
    broken["import_profiles"][0]["fields"] = ["damage"]
    path.write_text(json.dumps(broken))
    with pytest.raises(SettingsFormatError):
        store.load()


def test_csv_range_can_select_beyond_the_bounded_initial_preview(
    tmp_path: Path,
) -> None:
    """CSV selections can target distant rows without importing a whole large source.

    Args:
        tmp_path: Generated private delimited file with unrelated earlier rows.

    Returns:
        None; exact range values and source bytes survive bounded streaming selection.
    """
    path = tmp_path / "long.csv"
    rows = ["name;arm;force;count"] + [f"Row {i};30;49.05;100" for i in range(1, 2501)]
    path.write_text("\n".join(rows), encoding="utf-8")
    original = path.read_bytes()
    reader = SpreadsheetValueReader()
    profile = ImportProfile(AssessmentKind.LIFFT, delimiter=";")
    initial = reader.read(str(path), profile)
    assert len(initial.rows) == 2000 and initial.cell_range == "A1:D2000"
    selected = reader.read(str(path), profile, cell_range="A2401:D2402")
    assert selected.rows[0][0] == "Row 2400" and len(selected.rows) == 2
    assert path.read_bytes() == original
    with pytest.raises(ValueError):
        reader.read(str(path), profile, cell_range="A3000:B3001")


def test_chart_only_tabs_are_listed_but_never_treated_as_input_cells(
    tmp_path: Path,
) -> None:
    """Workbooks containing chart sheets still open a real data worksheet by default.

    Args:
        tmp_path: Generated workbook with a first-position chart-only tab.

    Returns:
        None; chart tabs report a policy error rather than an AttributeError.
    """
    from openpyxl.chart import BarChart, Reference

    path = tmp_path / "charts.xlsx"
    book = Workbook()
    page = book.active
    page["A1"] = "Value"
    page["A2"] = 1
    chart = BarChart()
    chart.add_data(
        Reference(page, min_col=1, min_row=1, max_row=2), titles_from_data=True
    )
    tab = book.create_chartsheet("Chart")
    tab.add_chart(chart)
    book.move_sheet("Chart", offset=-1)
    book.save(path)
    book.close()
    reader = SpreadsheetValueReader()
    profile = ImportProfile(AssessmentKind.LIFFT)
    result = reader.read(str(path), profile)
    assert result.sheet == "Sheet" and "Chart" in result.sheets
    with pytest.raises(ValueError, match="data worksheet"):
        reader.read(str(path), profile, "Chart")


@pytest.mark.parametrize("version", [6, 7])
def test_recent_legacy_preferences_load_without_import_data_or_rewrite(
    tmp_path: Path, version: int
) -> None:
    """Both recent pre-import formats preserve unrelated settings and upgrade on Save.

    Args:
        tmp_path: Private personal settings location.
        version: Historical Undo/result-animation preference formats.

    Returns:
        None; loading keeps old bytes; explicit Save adds empty import profiles.
    """
    import json

    path = tmp_path / "legacy.json"
    store = JsonSettingsStore(path)
    original = UserSettings(
        language=Language.SPANISH,
        default_units=MeasurementSystem.METRIC,
        recent_documents=("Muñoz.ergprj",),
        undo_limit=12,
    )
    store.save(original)
    payload = json.loads(path.read_text())
    payload["version"] = version
    payload.pop("import_profiles")
    payload.pop("assessment_columns")
    payload.pop("highs_single_tool", None)
    if version < 7:
        payload.pop("animated_risk_gauge")
        payload.pop("animated_cumulative_damage")
    path.write_text(json.dumps(payload))
    before = path.read_bytes()
    loaded = store.load()
    assert loaded == original and loaded.import_profiles == ()
    assert path.read_bytes() == before
    store.save(loaded)
    assert json.loads(path.read_text())["version"] == 11
    assert store.load() == original
