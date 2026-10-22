"""English/Spanish labels for the original organization form.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from ergotools.application.settings import Language
from ergotools.presentation.desktop.worker_text import worker_text

# Owned English/Spanish UI wording; keys/captions never replace saved record identities.
_MESSAGES = {
    "Shifts in use": "Turnos en uso",
    (
        "Distinct shifts used by active Jobs or worker workplace "
        "assignments in this plant."
    ): (
        "Turnos distintos utilizados por trabajos activos o asignaciones de "
        "trabajadores en esta planta."
    ),
    "Organization Management": "Gestión de la organización",
    "Manage the workplace hierarchy and independent work shifts.": (
        "Administre la jerarquía de puestos y los turnos independientes."
    ),
    "Organization": "Organización",
    "Location hierarchy": "Jerarquía de ubicaciones",
    "Type": ("Tipo"),
    "Locations": "Ubicaciones",
    "Shifts": "Turnos",
    "New plant": "Nueva planta",
    "New shift": ("Nuevo turno"),
    "Add element": "Agregar elemento",
    "Select an item": "Seleccione un elemento",
    "Choose a location or shift to view its details.": (
        "Seleccione una ubicación o turno para ver sus datos."
    ),
    "Optional details": "Datos opcionales",
    "Required information": ("Información obligatoria"),
    "Note: Select an item to begin.": "Nota: Seleccione un elemento para comenzar.",
    "Plant name": "Nombre de la planta",
    "Section name": "Nombre de la sección",
    "Line name": ("Nombre de la línea"),
    "Station ID": "ID de la estación",
    "Shift ID": "ID del turno",
    "Description": "Descripción",
    "Location": "Ubicación",
    "Plant type": "Tipo de planta",
    "Area": "Área",
    "Not set": "Sin especificar",
    "Ends the following day": "Termina al día siguiente",
    "Use for an overnight shift ending at or before its start time.": (
        "Use esta opción para un turno nocturno que termina "
        "a la misma hora o antes de su inicio."
    ),
    (
        "24-hour time HH:mm (00:00-23:59). Type or use the arrows. "
        "Ctrl+A, Delete clears this optional time."
    ): (
        "Hora de 24 horas HH:mm (00:00-23:59). Escriba o use las flechas. "
        "Ctrl+A, Suprimir borra esta hora opcional."
    ),
    (
        "End time must be later than start time. "
        "Select Ends the following day for an overnight shift."
    ): (
        "La hora de fin debe ser posterior a la de inicio. "
        "Seleccione Termina al día siguiente para un turno nocturno."
    ),
    (
        "For an overnight shift, end time must be at or before start time. "
        "Otherwise clear Ends the following day."
    ): (
        "En un turno nocturno, la hora de fin debe ser igual o anterior "
        "a la de inicio. "
        "De lo contrario, desmarque Termina al día siguiente."
    ),
    "Start time (24 h, HH:mm)": "Hora de inicio (24 h, HH:mm)",
    "End time (24 h, HH:mm)": "Hora de fin (24 h, HH:mm)",
    "Use 24-hour time HH:mm (00:00-23:59), or clear the time.": (
        "Use la hora de 24 horas HH:mm (00:00-23:59), o borre la hora."
    ),
    ("Production capacity"): ("Capacidad de producción"),
    "Operational duration (hours/minutes)": "Duración operativa (horas/minutos)",
    "Opening date": "Fecha de apertura",
    "Years of operation": "Años de operación",
    ("Capacity"): ("Capacidad"),
    "Creation date": "Fecha de creación",
    "Products": "Productos",
    "Cycle time (sec)": "Tiempo de ciclo (s)",
    "Number of operators": "Cantidad de operadores",
    "Shift type": "Tipo de turno",
    "Tasks performed": "Tareas realizadas",
    "Product output": ("Producción"),
    "Downtime (hrs)": "Tiempo inactivo (h)",
    "Notes": "Notas",
    "Top-level record": "Registro de nivel superior",
    "New section": "Nueva sección",
    "New line": "Nueva línea",
    "New station": ("Nueva estación"),
    "Edit plant": "Editar planta",
    "Edit section": "Editar sección",
    "Edit line": ("Editar línea"),
    "Edit station": "Editar estación",
    "Edit shift": "Editar turno",
    "Identifiers cannot be renamed because related records may depend on them.": (
        "Los identificadores no pueden cambiar porque otros "
        "registros pueden depender de ellos."
    ),
    "Note: Required identifiers must be unique within their parent location.": (
        "Nota: Los identificadores deben ser únicos dentro de su ubicación superior."
    ),
    "Note: Select a plant, section, or line before adding a child location.": (
        "Nota: Seleccione una planta, sección o línea antes de agregar un elemento."
    ),
    "Note: Stations are the final level of the location hierarchy.": (
        "Nota: Las estaciones son el último nivel de la jerarquía."
    ),
    "Note: Select the parent location before creating this record.": (
        "Nota: Seleccione la ubicación superior antes de crear el registro."
    ),
    "Note: An identifier is required.": "Nota: El identificador es obligatorio.",
    "Note: Changes accepted. Use the main Save to write the project.": (
        "Nota: Cambios aceptados. Use Guardar en la ventana principal."
    ),
    "Note: Record saved successfully.": "Nota: Registro guardado correctamente.",
    "Note: Deletion completed.": "Nota: Eliminación completada.",
    "Delete record": "Eliminar registro",
    (
        "Delete this record and its child locations? Referenced "
        "workplaces cannot be deleted."
    ): (
        "¿Desea eliminar este registro y sus ubicaciones "
        "inferiores? No se pueden eliminar puestos referenciados."
    ),
    (
        "Note: Could not save. Check identifiers, numeric values "
        "and referenced workplaces."
    ): ("Nota: Revise los identificadores, valores numéricos y puestos referenciados."),
    "Note: Unable to save changes. Please try again.": (
        "Nota: No se pudieron guardar los cambios. Inténtelo de nuevo."
    ),
    (
        "Expand the hierarchy and select a plant, section, line, or"
        " station to view its details."
    ): (
        "Expanda la jerarquía y seleccione una planta, sección, "
        "línea o estación para ver sus datos."
    ),
    "Select a shift to view or edit its independent schedule information.": (
        "Seleccione un turno para ver o editar su información independiente."
    ),
    "Manage the Plant > Section > Line > Station hierarchy.": (
        "Administre la jerarquía Planta > Sección > Línea > Estación."
    ),
    "Manage shifts, which are independent from the location hierarchy.": (
        "Administre turnos independientes de la jerarquía de ubicaciones."
    ),
    "Create a new top-level plant. On the Shifts tab, create a new shift.": (
        "Cree una planta. En la pestaña Turnos, cree un turno."
    ),
    "Add a new element at the next hierarchy level beneath the selected location.": (
        "Agregue un elemento bajo la ubicación seleccionada."
    ),
    "Delete the selected organization record after confirmation.": (
        "Elimine el registro seleccionado tras confirmar."
    ),
    "Show or hide descriptive and operational fields.": (
        "Muestre u oculte los datos descriptivos y operativos."
    ),
    "Validation, guidance, and save-result messages appear here.": (
        "Aquí aparecen los mensajes de validación, ayuda y guardado."
    ),
    "Discard unsaved field changes and reload the selected record.": (
        "Descarte los cambios y recargue el registro seleccionado."
    ),
    "Save the required identifier and any optional organization details.": (
        "Guarde el identificador y los datos opcionales."
    ),
    "Close Organization Management and return to the assessment.": (
        "Cierre esta ventana y vuelva a la evaluación."
    ),
    "Select this item to view or edit its information.": (
        "Seleccione este elemento para ver o editar sus datos."
    ),
}


def organization_text(source: str, language: Language) -> str:
    """Resolve form labels independently of saved user text and identities.

    Args:
        source: English reference UI wording or earlier project path, as stated by this
            operation; user values are retained literally.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized organization caption, using shared worker wording when applicable and
        preserving unknown source text.
    """
    if language is Language.ENGLISH:
        return source
    return _MESSAGES.get(source, worker_text(source, language))
