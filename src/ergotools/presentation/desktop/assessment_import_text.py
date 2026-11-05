"""Localized import diagnostics, retaining literal file/cell details where needed.

Presentation-only text. Scientific/input parser messages retain their existing shared
translator; file/import policy failures have explicit English/Spanish counterparts.
"""

from ergotools.domain.assessments.validation import DraftError
from ergotools.domain.language import Language
from ergotools.presentation.desktop.assessment_task_text import task_input_error

# Exact portable/adapter policy messages, translated without altering source values.
_IMPORT_ERRORS = {
    "Choose a data worksheet; this sheet has no tabular cells.": (
        "Elija una hoja de datos; esta hoja no contiene celdas de tabla."
    ),
    "Range is outside the source data.": "El rango está fuera de los datos de origen.",
    ("Select at most 2000 rows and 100 source columns."): (
        "Seleccione hasta 2000 filas y 100 columnas de origen."
    ),
    ("The selected range contains no values."): (
        "El rango seleccionado no contiene valores."
    ),
    "Invalid import profile choices.": "Opciones de importación no válidas.",
    ("Map each allowed input column only once."): (
        "Asigne cada entrada permitida una sola vez."
    ),
    ("Empty or oversized source data."): (
        "Los datos están vacíos o exceden el límite de vista previa."
    ),
    ("Choose one valid separator character."): (
        "Elija un solo carácter de separación válido."
    ),
    ("Invalid source quoting; review separator and quotes."): (
        "Comillas no válidas; revise el separador y las comillas."
    ),
    ("Preview supports up to 2000 rows and 100 source columns."): (
        "La vista admite hasta 2000 filas y 100 columnas de origen."
    ),
    ("Invalid thousands grouping; review number format."): (
        "Agrupación de miles no válida; revise el formato numérico."
    ),
    ("Source columns do not match this tool's saved mapping."): (
        "Las columnas no coinciden con la configuración guardada para esta herramienta."
    ),
    "Unsupported destination input.": "Entrada de destino no admitida.",
    ("Header units disagree: use cm/N or in/lbf; kg is mass."): (
        "Unidades incompatibles: use cm/N o in/lbf; kg es masa."
    ),
    ("Load is force (N/lbf), not mass (kg)."): (
        "La carga es fuerza (N/lbf), no masa (kg)."
    ),
    ("Choose the text encoding; the file is not valid in this encoding."): (
        "Elija la codificación; el archivo no es válido con esta opción."
    ),
    ("Source files must be smaller than 32 MB."): (
        "El archivo de origen debe ser menor de 32 MB."
    ),
    ("Text file exceeds the preview limit."): (
        "El archivo de texto excede el límite de vista previa."
    ),
    "Choose CSV, TSV or XLSX cell data.": "Elija datos de celdas en CSV, TSV o XLSX.",
    ("The selected worksheet is unavailable."): (
        "La hoja seleccionada no está disponible."
    ),
    "Use a rectangle such as B4:F25.": "Use un rectángulo como B4:F25.",
    ("Select at most 2000 rows and 100 columns inside the worksheet."): (
        "Seleccione hasta 2000 filas y 100 columnas dentro de la hoja."
    ),
    ("The workbook is unreadable or has no usable worksheets."): (
        "El libro no se puede leer o no tiene hojas utilizables."
    ),
}


def assessment_import_error(
    error: OSError | ValueError | DraftError, language: Language
) -> str:
    """Explain a staged import failure without translating names or accepting data.

    Args:
        error: Structured input, explicit import policy or native file failure.
        language: Selected presentation language.

    Returns:
        Localized known error; unexpected file details remain visible for correction.
    """
    message = str(error)
    if language is Language.SPANISH and message in _IMPORT_ERRORS:
        return _IMPORT_ERRORS[message]
    if isinstance(error, OSError):
        return (
            "No se pudo leer el archivo: "
            if language is Language.SPANISH
            else "Could not read the file: "
        ) + message
    return task_input_error(error, language)
