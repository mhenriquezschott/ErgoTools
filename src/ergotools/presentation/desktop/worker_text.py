"""English/Spanish text for the original worker-management controls.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from ergotools.application.settings import Language

# Owned English/Spanish UI wording; keys/captions never replace saved record identities.
_MESSAGES = {
    "Associate assessment": "Asociar evaluación",
    "{total} workplace assignment · {count} with a Job": (
        "{total} asignación de lugar · {count} con trabajo"
    ),
    "{total} workplace assignments · {count} with a Job": (
        "{total} asignaciones de lugar · {count} con trabajo"
    ),
    "Job (optional)": ("Trabajo (opcional)"),
    "Workplace hierarchy": ("Jerarquía de lugares de trabajo"),
    ("Choose the workplace and shift for {worker_id}, then optionally a Job."): (
        "Seleccione el lugar y turno para {worker_id}; después, un trabajo opcional."
    ),
    ("Existing workplace assignment will be reused; its Job stays unchanged."): (
        "Se reutilizará la asignación de lugar existente sin cambiar su trabajo."
    ),
    ("A Job is optional. Only Jobs available at this workplace and shift are shown."): (
        "El trabajo es opcional. Solo se muestran los disponibles en este "
        "lugar y turno."
    ),
    (
        "Select a station and shift. Create them in Organization if none are available."
    ): ("Seleccione una estación y un turno. Si no existen, créelos en Organización."),
    "Workplace assignment removed; existing assessments kept.": (
        "Asignación de lugar quitada; se conservan las evaluaciones existentes."
    ),
    (
        "Existing workplace assignment has a different Job; change it in "
        "Worker Management."
    ): (
        "La asignación existente tiene otro trabajo; cámbielo en Gestión "
        "de trabajadores."
    ),
    "Job placement does not match the selected workplace.": (
        "El trabajo no corresponde al lugar y turno seleccionados."
    ),
    "Select a real workplace and shift.": ("Seleccione un lugar y turno existentes."),
    ("Delete the selected worker after confirmation. Undo can restore it."): (
        "Eliminar al trabajador seleccionado tras confirmar. Deshacer "
        "permite restaurarlo."
    ),
    "Changes could not be accepted. Your entries are kept for retry.": (
        "No se pudieron aceptar los cambios. Se conservan para reintentar."
    ),
    "Enter a Worker ID; Add worker or Close accepts the record.": (
        "Ingrese un ID; Agregar trabajador o Cerrar acepta el registro."
    ),
    "Enter a Worker ID before adding assignments.": (
        "Ingrese un ID de trabajador antes de agregar asignaciones."
    ),
    "Worker changes accepted. Use the main Save to write the project.": (
        "Cambios aceptados. Use Guardar en la ventana principal para "
        "guardar el proyecto."
    ),
    "Add worker": ("Agregar trabajador"),
    "Accept this worker and start another.": (
        "Aceptar este trabajador y comenzar otro."
    ),
    "Actions": ("Acciones"),
    "Change assignment": ("Cambiar asignación"),
    "Remove assignment": ("Quitar asignación"),
    "Remove this active assignment? Existing assessments will be kept.": (
        "¿Quitar esta asignación activa? Se conservarán las evaluaciones existentes."
    ),
    "Save dropdown changes before changing or removing an assignment.": (
        "Guarde los cambios de las listas antes de cambiar o quitar una asignación."
    ),
    "Assignment removed; existing assessments kept.": (
        "Asignación quitada; evaluaciones existentes conservadas."
    ),
    "Workplace assignment changed; existing assessments kept.": (
        "Asignación cambiada; evaluaciones existentes conservadas."
    ),
    "Select an active assignment belonging to this Worker.": (
        "Seleccione una asignación activa de este trabajador."
    ),
    "Selected Job placement is unavailable.": (
        "La ubicación de trabajo seleccionada no está disponible."
    ),
    ("This Worker already has an assignment at the selected workplace and shift."): (
        "Este trabajador ya tiene una asignación en el lugar y turno seleccionados."
    ),
    "Note: {message}": ("Nota: {message}"),
    "Enter a Worker ID and save the new worker.": (
        "Ingrese un ID y guarde al nuevo trabajador."
    ),
    "Worker Management": ("Gestión de trabajadores"),
    (
        "Find a worker or create a new record. Worker ID is required; all "
        "other details are optional."
    ): (
        "Busque un trabajador o cree un registro. El ID es obligatorio; "
        "los demás datos son opcionales."
    ),
    "Workers": ("Trabajadores"),
    "Search by ID or name": ("Buscar por ID o nombre"),
    "Worker ID": ("ID del trabajador"),
    "Name": ("Nombre"),
    "Sex": ("Sexo"),
    "Age": ("Edad"),
    "All": ("Todos"),
    "Worker": ("Trabajador"),
    "First": ("Primera"),
    "Prev": ("Anterior"),
    "Next": ("Siguiente"),
    "Last": ("Última"),
    "Worker details": ("Datos del trabajador"),
    "Workplace assignments": ("Lugares de trabajo"),
    "Required information": ("Información obligatoria"),
    "Optional details": ("Datos opcionales"),
    "First name": ("Nombre"),
    "Last name": ("Apellido"),
    "Date of birth": ("Fecha de nacimiento"),
    "Calculated age": ("Edad calculada"),
    "Date of hiring": ("Fecha de contratación"),
    "Height (cm)": ("Estatura (cm)"),
    "Height (in)": ("Estatura (in)"),
    "Weight (kg)": ("Peso (kg)"),
    "Weight (lb)": ("Peso (lb)"),
    "Not provided": ("Sin especificar"),
    "Not available": ("No disponible"),
    "Female": ("Femenino"),
    "Male": ("Masculino"),
    "Outside US": ("Fuera de EE. UU."),
    "New worker": ("Nuevo trabajador"),
    "Save changes": ("Guardar cambios"),
    "Delete": ("Eliminar"),
    "Cancel": ("Cancelar"),
    "Close": ("Cerrar"),
    "Search": ("Buscar"),
    "Assigned workplaces": ("Lugares asignados"),
    "Assign workplace…": ("Asignar lugar…"),
    "Assign workplace": ("Asignar lugar de trabajo"),
    "Plant": ("Planta"),
    "Section": ("Sección"),
    "Line": ("Línea"),
    "Station": ("Estación"),
    "Shift": ("Turno"),
    "Job": ("Trabajo"),
    "Job ID": ("ID del trabajo"),
    "Job name": ("Nombre del trabajo"),
    "Select a worker to review or edit its information.": (
        "Seleccione un trabajador para revisar o editar sus datos."
    ),
    "Worker record loaded and ready to edit.": (
        "Registro cargado y listo para editar."
    ),
    "Worker changes saved.": ("Datos del trabajador guardados."),
    "Worker deleted.": ("Trabajador eliminado."),
    "Worker ID is required.": ("El ID del trabajador es obligatorio."),
    "Worker ID cannot contain spaces.": (
        "El ID del trabajador no puede contener espacios."
    ),
    "Workers with saved assignments cannot be deleted.": (
        "No se pueden eliminar trabajadores con asignaciones guardadas."
    ),
    "Select a Worker before editing workplace assignments.": (
        "Seleccione un trabajador para editar sus lugares de trabajo."
    ),
    "Select a Worker before assigning a workplace.": (
        "Seleccione un trabajador antes de asignar un lugar de trabajo."
    ),
    "No Job": ("Sin trabajo"),
    "Placement unavailable": ("Puesto no disponible"),
    "{age} years": ("{age} años"),
    "{count} workers": ("{count} trabajadores"),
    "Page {page} of {total}": ("Página {page} de {total}"),
    "Confirm Deletion": ("Confirmar eliminación"),
    "Are you sure you want to delete this worker?": (
        "¿Desea eliminar este trabajador?"
    ),
    "Unable to save worker changes. Please try again.": (
        "No se pudieron guardar los cambios. Inténtelo de nuevo."
    ),
    (
        "Workplace assigned. Assessments are unchanged; select an assessment"
        " context in the main window to open or create one."
    ): (
        "Lugar asignado. Las evaluaciones no cambian; seleccione un contexto de"
        " evaluación en la ventana principal para abrir o crear una."
    ),
    "Filter the worker list by Worker ID, first name, or last name.": (
        "Filtre la lista por ID, nombre o apellido."
    ),
    "Select a row to view or edit that worker's details.": (
        "Seleccione una fila para ver o editar los datos del trabajador."
    ),
    "Filter workers by the first letter of their first or last name.": (
        "Filtre por la primera letra del nombre o apellido."
    ),
    "Show all workers.": ("Mostrar todos los trabajadores."),
    "The arrow buttons move one worker at a time.": (
        "Las flechas avanzan un trabajador por vez."
    ),
    "Go to the first worker.": ("Ir al primer trabajador."),
    "Go to the previous worker.": ("Ir al trabajador anterior."),
    "Go to the next worker.": ("Ir al siguiente trabajador."),
    "Go to the last worker.": ("Ir al último trabajador."),
    "Show the first page of workers.": ("Mostrar la primera página."),
    "Show the previous page of workers.": ("Mostrar la página anterior."),
    "Show the next page of workers.": ("Mostrar la siguiente página."),
    "Show the last page of workers.": ("Mostrar la última página."),
    "Current worker-list page and total number of pages.": (
        "Página actual y cantidad total de páginas."
    ),
    "Required. Enter a unique Worker ID without spaces.": (
        "Obligatorio. Ingrese un ID único sin espacios."
    ),
    "Optional worker first name.": ("Nombre opcional del trabajador."),
    "Optional worker last name.": ("Apellido opcional del trabajador."),
    "Worker's year of birth. Age is calculated automatically.": (
        "Año de nacimiento. La edad se calcula automáticamente."
    ),
    (
        "Optional complete date of birth. Age is calculated automatically "
        "when provided."
    ): ("Fecha de nacimiento opcional. La edad se calcula automáticamente."),
    "Calculated automatically when a date of birth is provided.": (
        "Se calcula automáticamente si se indica la fecha de nacimiento."
    ),
    "Optional worker sex used for filtering and the PLOT marker shape.": (
        "Sexo opcional utilizado en filtros y marcadores de PLOT."
    ),
    ("Show or hide optional identity, employment, and body measurement fields."): (
        "Mostrar u ocultar datos de identidad, empleo y medidas corporales."
    ),
    (
        "Optional worker height. Values use the project's configured "
        "measurement system."
    ): ("Estatura opcional en el sistema de unidades seleccionado."),
    (
        "Optional worker weight. Values use the project's configured "
        "measurement system."
    ): ("Peso opcional en el sistema de unidades seleccionado."),
    "Optional street or workplace address.": ("Dirección opcional."),
    "Optional city.": ("Ciudad opcional."),
    (
        "Optional state or region. US states are listed when United States is selected."
    ): (
        "Estado o región opcional. Estados de EE. UU. disponibles al "
        "seleccionar United States."
    ),
    "Optional country.": ("País opcional."),
    "Optional postal or ZIP code.": ("Código postal opcional."),
    "Optional email address.": ("Correo electrónico opcional."),
    "Optional employment start date.": ("Fecha de inicio del empleo opcional."),
    "Previous month": ("Mes anterior"),
    "Next month": ("Mes siguiente"),
    ("Start a blank worker record. Unsaved edits in the form are cleared."): (
        "Crear un registro vacío. Se descartan los cambios sin guardar."
    ),
    "Save this worker and all entered optional details to the project.": (
        "Guardar al trabajador y sus datos opcionales en el proyecto."
    ),
    "Permanently delete the selected worker after confirmation.": (
        "Eliminar al trabajador seleccionado tras confirmar."
    ),
    ("Discard the current new-record form and return to the first worker."): (
        "Descartar el formulario actual y volver al primer trabajador."
    ),
    "Close Worker Management and return to the assessment window.": (
        "Cerrar y volver a la ventana de evaluación."
    ),
    "Assign this Worker to a workplace and shift; a Job is optional.": (
        "Asignar al trabajador a un lugar y turno; el trabajo es opcional."
    ),
    (
        "Choose an optional Job for each workplace assignment using a "
        "compatible Job Placement."
    ): ("Elegir un trabajo opcional disponible en cada lugar y turno."),
    (
        "Choose the workplace and shift for {worker_id}. An existing assignment "
        "is reused; otherwise one is created with the optional Job on acceptance."
    ): "Elija el lugar y turno para {worker_id}. Se reutiliza la asignación existente; "
    "si no existe, se crea al aceptar con el trabajo opcional.",
    "Type": "Tipo",
    "Plant for this workplace assignment.": (
        "Planta de esta asignación de lugar de trabajo."
    ),
    "Section within the selected Plant.": ("Sección dentro de la planta seleccionada."),
    "Line within the selected Section.": ("Línea dentro de la sección seleccionada."),
    "Station where this worker is assigned.": (
        "Estación donde está asignado este trabajador."
    ),
    "Shift for this workplace assignment.": (
        "Turno de esta asignación de lugar de trabajo."
    ),
    "Change or remove this workplace assignment.": (
        "Cambie o quite esta asignación de lugar de trabajo."
    ),
}


def worker_text(source: str, language: Language) -> str:
    """Translate UI text while leaving saved identities and country names intact.

    Args:
        source: English reference UI wording or earlier project path, as stated by this
            operation; user values are retained literally.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized known worker UI caption or alphabet explanation; unknown text and
        country/record values remain literal.
    """
    if language is Language.ENGLISH:
        return source
    prefix = "Show workers whose first or last name begins with "
    if source.startswith(prefix):
        return (
            "Mostrar trabajadores cuyo nombre o apellido comienza con "
            + source[len(prefix) :]
        )
    return _MESSAGES.get(source, source)
