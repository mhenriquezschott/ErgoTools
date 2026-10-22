"""Worker Transfer captions; caller-owned record values are never translated.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from ergotools.application.settings import Language

# Spanish owned interface wording; unknown English captions retain the documented
# fallback.
_SPANISH = {
    ("Move"): ("Mover"),
    ("Copy"): ("Copiar"),
    ("Transfer preview: "): ("Vista previa: "),
    ("Select at least one available assessment tool."): (
        "Elija al menos una herramienta disponible."
    ),
    ("Select a destination worker."): ("Elija un trabajador de destino."),
    ("Select a destination station from the workplace hierarchy."): (
        "Elija una estación de destino en la jerarquía."
    ),
    ("{mode} {count} selected tools to {worker} at {path}, shift {shift}."): (
        "{mode} {count} herramientas a {worker} en {path}, turno {shift}."
    ),
    ("Transfer Assessment Data"): ("Transferir datos de evaluación"),
    ("Transfer assessment data"): ("Transferir datos de evaluación"),
    ("1. Source"): ("1. Origen"),
    ("2. Operation"): ("2. Operación"),
    ("3. Destination"): ("3. Destino"),
    ("Copy data"): ("Copiar datos"),
    ("Move data"): ("Mover datos"),
    ("Available tools"): ("Herramientas disponibles"),
    ("Include"): ("Incluir"),
    ("Assessment tool"): ("Herramienta"),
    ("Worker ID"): ("ID trabajador"),
    ("Last name"): ("Apellido"),
    ("First name"): ("Nombre"),
    ("Workplace and shift"): ("Lugar y turno"),
    ("Workplace hierarchy"): ("Jerarquía"),
    ("Type"): ("Tipo"),
    ("Shift"): ("Turno"),
    ("Transfer selected tools"): ("Transferir herramientas"),
    ("Search worker ID or name"): ("Buscar ID o nombre"),
    ("Cancel"): ("Cancelar"),
    ("Plant"): ("Planta"),
    ("Section"): ("Sección"),
    ("Line"): ("Línea"),
    ("Station"): ("Estación"),
    ("Select tools and a complete destination."): ("Elija herramientas y destino."),
    ("Confirm transfer"): ("Confirmar transferencia"),
    ("Transfer failed"): ("Error de transferencia"),
    ("Transfer complete"): ("Transferencia completada"),
    ("All"): ("Todos"),
    ("Reuse selected ergonomic assessments for another worker, workplace, or shift."): (
        "Reutilice evaluaciones para otro trabajador, puesto o turno."
    ),
    ("The active worker and workplace in the main window are used as the source."): (
        "El trabajador y el puesto de la ventana principal son el origen."
    ),
    ("Copy keeps the source data. Move removes it after the destination is created."): (
        "Copiar conserva los datos de origen. Mover los elimina tras crear el destino."
    ),
    (
        "Move is completed as one database transaction. If an"
        "y selected destination conflicts, nothing is changed"
        "."
    ): (
        "Mover se realiza en una sola transacción. Si existe "
        "un conflicto en el destino, no se modifica nada."
    ),
    (
        "Choose a worker, then select the station and shift t"
        "hat should receive the assessment."
    ): ("Elija el trabajador, la estación y el turno que recibirán la evaluación."),
    (
        "No saved assessment data exists for this worker and "
        "workplace.\n\nReturn to the main window and select a s"
        "ource context that contains tool data."
    ): (
        "No hay evaluaciones guardadas para este trabajador y"
        " puesto.\n\nVuelva a la ventana principal y elija un c"
        "ontexto con datos."
    ),
    ("Select the assessment tools to copy or move."): (
        "Elija las herramientas que desea copiar o mover."
    ),
    ("Create the selected assessments at the destination and keep the originals."): (
        "Cree las evaluaciones seleccionadas en el destino y conserve las originales."
    ),
    ("Create the selected assessments at the destination and remove the originals."): (
        "Cree las evaluaciones seleccionadas en el destino y elimine las originales."
    ),
    ("Filter destination workers while typing."): (
        "Filtre los trabajadores de destino al escribir."
    ),
    ("Show all workers"): ("Mostrar todos los trabajadores"),
    ("Show last names beginning with {letter}"): (
        "Mostrar apellidos que comienzan con {letter}"
    ),
    ("Select the worker who should receive the assessment data."): (
        "Elija el trabajador que recibirá los datos de evaluación."
    ),
    ("Expand the hierarchy and select the destination station."): (
        "Despliegue la jerarquía y elija la estación de destino."
    ),
    ("Select the destination work shift."): ("Elija el turno de destino."),
    ("Close without changing assessment data."): (
        "Cerrar sin modificar los datos de evaluación."
    ),
    ("Perform the selected copy or move operation."): (
        "Realizar la operación de copiar o mover seleccionada."
    ),
    ("Lifting Fatigue Failure Tool"): ("Herramienta de fatiga por levantamiento"),
    ("Distal Upper Extremity Tool"): ("Herramienta de extremidad superior distal"),
    ("Shoulder Tool"): ("Herramienta de hombro"),
    ("Include {tool} in this operation."): ("Incluir {tool} en esta operación."),
    ("Destination already contains selected assessment data."): (
        "El destino ya contiene datos de las herramientas seleccionadas."
    ),
    ("Source and destination contexts are identical."): (
        "Los contextos de origen y destino son iguales."
    ),
    ("Selected source has no saved current version."): (
        "El origen seleccionado no tiene una versión actual guardada."
    ),
    (
        "The selected data could not be transferred. Reopen t"
        "he form and check the destination."
    ): (
        "No se pudieron transferir los datos. Vuelva a abrir "
        "la ventana y revise el destino."
    ),
}


def transfer_text(english: str, language: Language) -> str:
    """Translate owned captions while retaining English as the fallback language.

    Args:
        english: English UI text; saved user values are never translated by this helper.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Spanish owned caption when available, otherwise the unchanged English caption.
    """
    return _SPANISH.get(english, english) if language is Language.SPANISH else english
