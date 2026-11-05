"""English/Spanish task-name and clipboard captions, separate from literal data.

Presentation layer. Translate known validation messages and field identities only.
Task names, units and numeric values remain literal; unknown operational errors retain
useful original detail instead of being silently replaced by plausible success.
"""

from ergotools.application.assessment_clipboard import ClipboardRowError
from ergotools.application.settings import Language
from ergotools.domain.assessments.validation import DraftError
from ergotools.presentation.localization import Translator

# Stable editable-field identities; the name column is descriptive, not scientific.
_FIELDS = {
    "task_name": ("Task name", "Nombre de tarea"),
    "lever_arm": ("Lever arm", "Brazo de palanca"),
    "load": ("Load", "Carga"),
    "repetitions": ("Repetitions / work day", "Repeticiones / jornada"),
    "omni_res_scale": ("OMNI-Res scale", "Escala OMNI-Res"),
    "direction": ("Task type", "Tipo de tarea"),
}
# Application validation messages are stable contracts, not user-entered values.
_ERRORS = {
    "Job data changed; reload before editing.": (
        "Los datos del trabajo cambiaron; vuelva a cargar antes de editar."
    ),
    "Task paste was not accepted; no data was changed.": (
        "No se aceptó el pegado; no se modificaron datos."
    ),
    "Open an editable project before pasting task data.": (
        "Abra un proyecto editable antes de pegar datos de tareas."
    ),
    "Unsupported header units. Use cm/N or in/lbf.": (
        "Unidades de encabezado no admitidas. Use cm/N o in/lbf."
    ),
    "Clipboard selection is too large.": (
        "La selección del portapapeles es demasiado grande."
    ),
    "Clipboard cells have invalid quoting.": (
        "Las celdas tienen comillas incorrectas."
    ),
    "Paste a rectangular selection of at most 100 task rows.": (
        "Pegue una selección rectangular de hasta 100 tareas."
    ),
    "Paste cell values, not spreadsheet formulas.": (
        "Pegue valores de celdas, no fórmulas."
    ),
    "Task inputs must be nonnegative.": (
        "Los valores de las tareas no pueden ser negativos."
    ),
    "OMNI-Res must be a whole number from 0 to 10.": (
        "OMNI-Res debe ser un entero entre 0 y 10."
    ),
    "Choose an ST task type or code 0, 1 or 2.": (
        "Elija un tipo de tarea ST o código 0, 1 o 2."
    ),
    "Paste mapping, target row or task capacity is invalid.": (
        "Revise las columnas asignadas, la fila de destino y el límite de 100 tareas."
    ),
    "Task catalog is stale or has invalid definitions.": (
        "Los nombres de tareas cambiaron o contienen datos inválidos."
    ),
    "A reusable task is still referenced by an assessment.": (
        "Una evaluación todavía utiliza esta tarea reutilizable."
    ),
    "Reusable task names require the current project format.": (
        "Los nombres reutilizables requieren el formato de proyecto actual."
    ),
}


def task_field_caption(field: str, language: Language) -> str:
    """Resolve an editable field caption without modifying names or measurements.

    Args:
        field: Stable canonical input identity.
        language: English/Spanish display preference.

    Returns:
        Human-readable caption; unknown field identities remain literal.
    """
    captions = _FIELDS.get(field, (field, field))
    return captions[int(language is Language.SPANISH)]


def task_input_error(error: ValueError | DraftError, language: Language) -> str:
    """Explain a known task-input failure using the existing validation translator.

    Args:
        error: Structured numeric issue or known application validation error.
        language: Current interface language, independent of numeric decimal convention.

    Returns:
        Localized message with a field caption where available; source text is literal.
    """
    if isinstance(error, ClipboardRowError):
        prefix = "Tarea" if language is Language.SPANISH else "Task"
        return f"{prefix} {error.row_index + 1}: " + task_input_error(
            error.detail, language
        )
    if isinstance(error, DraftError):
        return (
            task_field_caption(error.issue.field, language)
            + ": "
            + Translator(language).text(error.issue.code)
        )
    message = str(error)
    return _ERRORS.get(message, message) if language is Language.SPANISH else message
