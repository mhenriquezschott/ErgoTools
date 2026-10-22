"""English/Spanish text for reviewed original shared navigation.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from ergotools.application.settings import Language

# Owned English/Spanish UI wording; keys/captions never replace saved record identities.
_MESSAGES = {
    "Organization": "Organización",
    "Manage workplace organization.": (
        "Administrar la organización del lugar de trabajo."
    ),
    "Manage Jobs and current risk values.": (
        "Administrar trabajos y valores actuales de riesgo."
    ),
    "Undo": "Deshacer",
    "Redo": "Rehacer",
    "Undo the previous edit.": "Deshacer la edición anterior.",
    "Redo the next edit.": "Rehacer la siguiente edición.",
    "Follow worker": "Seguir al trabajador",
    "Keep context": "Mantener contexto",
    "Restore this worker's last-used valid assessment context.": (
        "Restaurar el último contexto válido de evaluación del trabajador."
    ),
    "Keep this workplace while navigating workers.": (
        "Mantener este lugar al navegar entre trabajadores."
    ),
    "No saved ST assessment for this worker.": (
        "No hay una evaluación ST guardada para este trabajador."
    ),
    "No saved DUET assessment for this worker.": (
        "No hay una evaluación DUET guardada para este trabajador."
    ),
    "Job performed in this assessment context.": (
        "Trabajo de este contexto de evaluación."
    ),
    "The ergonomic assessment tool currently selected.": (
        "Herramienta ergonómica seleccionada."
    ),
    "The measurement system used by the current project.": (
        "Sistema de unidades del proyecto actual."
    ),
    "The project currently open in Ergo Tools.": "Proyecto abierto en Ergo Tools.",
    "New": "Nuevo",
    "Open": "Abrir",
    "Save": "Guardar",
    "Jobs": "Trabajos",
    "Export": "Exportar",
    "Settings": "Configuración",
    "Help": "Ayuda",
    "Search": "Buscar",
    "Transfer": "Transferir",
    "Refresh": "Actualizar",
    "A-Z": "A-Z",
    "Worker": "Trabajador",
    "Workers": "Trabajadores",
    "Last name": "Apellido",
    "Assessment context": "Contexto de evaluación",
    "Standalone assessment": "Evaluación independiente",
    "Associate assessment...": "Asociar evaluación...",
    "View this worker's assessment without a workplace association.": (
        "Ver la evaluación del trabajador sin asociación a un lugar de trabajo."
    ),
    "Associate this saved assessment; its inputs and results stay unchanged.": (
        "Asociar esta evaluación guardada; sus datos y resultados no cambian."
    ),
    "Select assessment context": "Seleccionar contexto",
    "Manage organization": "Administrar organización",
    "No project loaded": "Sin proyecto abierto",
    "Current Project": "Proyecto actual",
    "Loaded": "Cargado",
    "Unclassified": "Sin clasificar",
    "Job": "Trabajo",
    "Tool": "Herramienta",
    "Units": "Unidades",
    "Imperial": "Imperial",
    "Metric": "Métrico",
    "Plant": "Planta",
    "Section": "Sección",
    "Line": "Línea",
    "Station": "Estación",
    "Shift": "Turno",
    "All": "Todos",
    "Create a new project.": "Cree un proyecto nuevo.",
    ("Open an existing Ergo Tools project."): (
        "Abra un proyecto existente de Ergo Tools."
    ),
    ("Save the current project and assessment data."): (
        "Guarde el proyecto y los datos de evaluación actuales."
    ),
    ("Open the Plant-Layout Organizational Tool."): (
        "Abra la herramienta de organización de la distribución de planta."
    ),
    ("Manage Jobs, risk values, calculators, and workplace availability."): (
        "Administre trabajos, riesgos, calculadoras y disponibilidad de puestos."
    ),
    ("Open the Job Rotation Optimization Tool."): (
        "Abra la herramienta de optimización de rotaciones."
    ),
    ("Export data from the selected ergonomic tool."): (
        "Exporte los datos de la herramienta ergonómica seleccionada."
    ),
    ("Configure the number of task rows and application options."): (
        "Configure las filas de tareas y las opciones de la aplicación."
    ),
    "Open the Ergo Tools user manual.": "Abra el manual de Ergo Tools.",
    ("Worker associated with the assessment currently shown."): (
        "Trabajador asociado con la evaluación mostrada."
    ),
    "Change worker ordering.": ("Cambie el orden de los trabajadores."),
    "Open Worker Management.": "Abra la gestión de trabajadores.",
    (
        "Find and open a saved assessment "
        "by worker, workplace, and the "
        "active ergonomic tool."
    ): (
        "Busque y abra una evaluación "
        "guardada por trabajador, puesto y "
        "herramienta activa."
    ),
    ("Transfer worker assessment data to another context."): (
        "Transfiera los datos de evaluación a otro contexto."
    ),
    ("Reload workers and assessment context values from the project."): (
        "Actualice los trabajadores y contextos de evaluación del proyecto."
    ),
    "First worker": "Primer trabajador",
    "Previous worker": "Trabajador anterior",
    "Next worker": "Trabajador siguiente",
    "Last worker": "Último trabajador",
    ("Filter the worker selector by the first letter of the last name."): (
        "Filtre los trabajadores por la inicial del apellido."
    ),
    ("Worker, Job, workplace, and shift associated with the active assessment."): (
        "Trabajador, trabajo, puesto y turno asociados con la evaluación activa."
    ),
    "Next workplace level": "Siguiente nivel del puesto",
    (
        "Select which classified Job and "
        "workplace assessment to view. This "
        "does not move data."
    ): ("Seleccione la evaluación de trabajo y puesto. Los datos no se trasladan."),
    ("Manage plants, sections, lines, stations, and shifts."): (
        "Administre plantas, secciones, líneas, estaciones y turnos."
    ),
    ("Select the worker whose assessment data you want to view or edit."): (
        "Seleccione el trabajador cuya evaluación desea ver o editar."
    ),
    "Show every worker": "Mostrar todos los trabajadores",
    "Show last names beginning with": "Mostrar apellidos que comienzan con",
    ("No saved LiFFT assessment for this worker."): (
        "Este trabajador no tiene una evaluación LiFFT guardada."
    ),
}


def navigation_text(text: str, language: Language) -> str:
    """Translate view text without touching stored names, identities or units.

    Args:
        text: Literal control text or user input; interpretation follows this method's
            stated policy.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized known navigation wording, otherwise the unchanged English source
        caption.
    """
    return _MESSAGES.get(text, text) if language is Language.SPANISH else text
