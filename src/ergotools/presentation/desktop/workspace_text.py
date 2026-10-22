"""Localized original workspace captions and tooltips.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from ergotools.application.settings import Language

# Spanish owned interface wording; unknown English captions retain the documented
# fallback.
_SPANISH = {
    "Individual Shoulder": "ST individual",
    "Shoulder Body Region": "Región corporal ST",
    "Shoulders": "Hombros",
    "Shoulder Individual Risk Score": "Puntuación de riesgo individual ST",
    "Probability of shoulder\noutcome": "Probabilidad de lesión\nde hombro",
    "Review required": "Revisión requerida",
    "Individual DUET": "DUET individual",
    "DUET Body Region": "Región corporal DUET",
    "Distal Upper Extremity": "Extremidad superior distal",
    "DUET Individual Risk Score": "Puntuación de riesgo individual DUET",
    "Probability of distal upper\nextremity outcome": (
        "Probabilidad de lesión de\nextremidad superior distal"
    ),
    "Individual LiFFT": "LiFFT individual",
    "Risk Level": "Nivel de riesgo",
    "Low": "Bajo",
    "Moderate": "Moderado",
    "Moderate High": "Moderado alto",
    "High": "Alto",
    "Not available": "No disponible",
    "Probability of high-risk\njob": ("Probabilidad de trabajo\nde alto riesgo"),
    "Cumulative damage": "Daño acumulado",
    "Key metrics": "Métricas clave",
    "Tasks": "Tareas",
    "Repetitions": "Repeticiones",
    "Average load": "Carga media",
    "Max moment": "Momento máximo",
    "Status": "Estado",
    "Ready": "Listo",
    "Incomplete": "Incompleto",
    "Assessment data is available.": ("Los datos de evaluación están disponibles."),
    ("Results include completed rows only."): (
        "Los resultados incluyen solo filas completas."
    ),
    "Calculation requires review.": "El cálculo requiere revisión.",
    "Enter context and task data.": ("Introduzca contexto y datos de tareas."),
    ("Select a context and enter task data."): (
        "Seleccione contexto e introduzca datos de tareas."
    ),
    "LiFFT Body Region": "Región corporal LiFFT",
    "Lower Back": "Zona lumbar",
    "Active Region": "Región activa",
    "LiFFT Individual Risk Score": ("Puntuación de riesgo individual LiFFT"),
    "Rotate": "Girar",
    "Zoom": "Ampliar",
    "Reset View": "Restablecer vista",
    "3D view unavailable": "Vista 3D no disponible",
    "Rotate the model clockwise.": ("Girar el modelo en sentido horario."),
    ("Zoom in on the active body region."): ("Ampliar la región corporal activa."),
    "Restore the initial model view.": ("Restaurar la vista inicial del modelo."),
    "Low Risk": "Riesgo bajo",
    "Moderate Risk": "Riesgo moderado",
    "Moderate High Risk": "Riesgo moderado alto",
    "High Risk": "Riesgo alto",
    (
        "Estimated individual probability"
        " for the adverse outcome calcula"
        "ted by the active ergonomic tool"
        "."
    ): ("Probabilidad individual estimada por la herramienta ergonómica activa."),
    ("Combined cumulative damage contribution from the entered tasks."): (
        "Daño acumulado combinado de las tareas introducidas."
    ),
    (
        "Cumulative damage scale: 0 at th"
        "e left, 1 at the midpoint, and v"
        "alues above 2 capped at >2."
    ): (
        "Escala de daño: 0 a la izquierda"
        ", 1 en el centro y valores super"
        "iores a 2 limitados a >2."
    ),
    ("A live summary of the task data entered for the active tool."): (
        "Resumen de los datos de tareas de la herramienta activa."
    ),
    ("Indicates whether the active assessment contains data that can be evaluated."): (
        "Indica si la evaluación activa contiene datos evaluables."
    ),
}


def workspace_text(text: str, language: Language) -> str:
    """Translate reviewed captions; preserve brand names and numeric range labels.

    Args:
        text: Literal control text or user input; interpretation follows this method's
            stated policy.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized known workspace caption, otherwise its unchanged source text
        (including brands/range labels).
    """
    return _SPANISH.get(text, text) if language is Language.SPANISH else text
