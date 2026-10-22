"""English/Spanish messages for migrated desktop components.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from ergotools.application.settings import Language

# Stable desktop message identities map to English/Spanish text; user data is literal.
_MESSAGES = {
    "migration_title": (
        "Project upgrade required",
        "Es necesario actualizar el proyecto",
    ),
    "migration_explanation": (
        "This project uses an earlier format. The separate migration tool can create "
        "a new self-contained project, including all plant images. Your original "
        "project and its folders will remain unchanged. Calculations are refreshed "
        "from the saved task inputs. The upgraded copy opens temporarily: use Save "
        "to choose its permanent file before closing.",
        "Este proyecto usa un formato anterior. La herramienta de migración "
        "independiente puede crear un proyecto autónomo con todas las imágenes "
        "de plantas. El proyecto original y sus carpetas no se modificarán. Los "
        "resultados se recalculan desde las tareas guardadas. La copia actualizada "
        "se abre temporalmente: use Guardar para elegir su archivo definitivo "
        "antes de cerrar.",
    ),
    "migration_cli": (
        "Or cancel and run the separate tool from a terminal "
        "(choose a new output file):",
        "También puede cancelar y ejecutar la herramienta desde una terminal "
        "(elija un archivo de salida nuevo):",
    ),
    "migration_cli_tip": (
        "Select and copy this command.",
        "Seleccione y copie este comando.",
    ),
    "migration_action": ("Migrate", "Migrar"),
    "migration_action_tip": (
        "Create and open a temporary upgraded copy.",
        "Crear y abrir una copia actualizada temporal.",
    ),
    "migration_cancel_tip": (
        "Keep the current project open.",
        "Mantener abierto el proyecto actual.",
    ),
    "migration_failed": (
        "Upgrade failed. The current project is unchanged. Check that the separate "
        "tool is available and the original folders are present. Details:",
        "No se pudo actualizar. El proyecto actual no se ha modificado. Compruebe "
        "que la herramienta independiente y las carpetas originales estén "
        "disponibles. Detalles:",
    ),
    "migration_saved_required": (
        "Upgraded copy opened. Use Save to choose its permanent file. "
        "After saving, the original database/image folders are no longer needed.",
        "Copia actualizada abierta. Use Guardar para elegir su archivo definitivo. "
        "Después de guardar, ya no necesita las carpetas originales "
        "de datos e imágenes.",
    ),
    "untitled_project": ("Untitled project", "Proyecto sin guardar"),
    "original_grid_ready": (
        "Enter task data, then Calculate.",
        "Ingrese los datos de las tareas y luego pulse Calcular.",
    ),
    "organization_management": (
        "Organization Management",
        "Gestión de la organización",
    ),
    "worker_management": ("Worker Management", "Gestión de trabajadores"),
    "context_create_assessment": (
        "No assessment exists for this tool and context. Create a blank assessment?",
        "No existe una evaluación de esta herramienta en este contexto. "
        "¿Crear una vacía?",
    ),
    "job_form_title": ("Job Management", "Gestión de trabajos"),
    "job_form_intro": (
        "Enter a Job ID, then define current risks. Main Save writes the project.",
        (
            "Ingrese un ID del trabajo y defina sus riesgos. "
            "Guardar principal escribe el proyecto."
        ),
    ),
    "job_form_jobs": ("Jobs", "Trabajos"),
    "job_form_id": ("Job ID", "ID del trabajo"),
    "job_form_select_tip": (
        "Select an existing job or enter an ID for a new job.",
        "Seleccione un trabajo existente o ingrese el ID de uno nuevo.",
    ),
    "job_form_first": ("First job", "Primer trabajo"),
    "job_form_previous": ("Previous job", "Trabajo anterior"),
    "job_form_next": ("Next job", "Trabajo siguiente"),
    "job_form_last": ("Last job", "Último trabajo"),
    "job_form_search": ("Search", "Buscar"),
    "job_form_details": ("Job details", "Datos del trabajo"),
    "job_form_workplaces_empty": ("Workplaces (0)", "Puestos (0)"),
    "job_form_workplaces": ("Workplaces ({count})", "Puestos ({count})"),
    "job_form_assign_tip": (
        "Assign this Job to one or more workplace contexts.",
        "Asigne este trabajo a uno o más puestos y turnos.",
    ),
    "job_form_name": ("Job name", "Nombre del trabajo"),
    "job_form_name_tip": (
        "Enter a descriptive name for this job.",
        "Ingrese un nombre descriptivo para este trabajo.",
    ),
    "job_form_description": ("Description", "Descripción"),
    "job_form_description_hint": (
        "Optional job description",
        "Descripción opcional del trabajo",
    ),
    "job_form_risk_help": (
        "Cumulative damage and calculated outcome probability",
        "Daño acumulado y probabilidad calculada del resultado",
    ),
    "job_form_measurements": ("Risk measurements", "Mediciones de riesgo"),
    "job_form_new_job": ("Add Job", "Agregar trabajo"),
    "job_form_new_status": ("New Job", "Nuevo trabajo"),
    "job_form_save": ("Save changes", "Guardar cambios"),
    "job_form_delete": ("Delete", "Eliminar"),
    "job_form_discard": ("Discard changes", "Descartar cambios"),
    "job_form_close": ("Close", "Cerrar"),
    "job_form_discard_tip": (
        "Discard unaccepted text. Use Undo for accepted edits.",
        "Descarte texto no aceptado. Use Deshacer para cambios aceptados.",
    ),
    "job_form_validation": ("Validation Error", "Error de validación"),
    "job_form_failure": (
        "The operation failed. Your form entries remain available. Please try again.",
        (
            "La operación falló. Los datos ingresados siguen "
            "disponibles. Inténtelo de nuevo."
        ),
    ),
    "job_form_success": ("Success", "Operación completada"),
    "job_form_saved": ("Job changes saved.", "Cambios del trabajo guardados."),
    "job_form_delete_title": ("Confirm Deletion", "Confirmar eliminación"),
    "job_form_delete_question": (
        "Are you sure you want to delete this job?",
        "¿Está seguro de que desea eliminar este trabajo?",
    ),
    "job_form_deleted": (
        "Job '{job_id}' has been deleted successfully.",
        "El trabajo '{job_id}' se ha eliminado correctamente.",
    ),
    "job_form_search_title": ("Search Job", "Buscar trabajo"),
    "job_form_search_label": ("Search by Job ID:", "Buscar por ID del trabajo:"),
    "job_form_no_match": ("No Match", "Sin coincidencias"),
    "job_form_not_found": (
        "No job found with the given criteria.",
        "No se encontró un trabajo con los criterios indicados.",
    ),
    "job_form_ok": ("OK", "Aceptar"),
    "job_form_cancel": ("Cancel", "Cancelar"),
    "job_form_yes": ("Yes", "Sí"),
    "job_form_no": ("No", "No"),
    "job_form_invalid_id": (
        "Job ID is required and cannot contain spaces.",
        "El ID del trabajo es obligatorio y no puede contener espacios.",
    ),
    "job_form_empty_id": (
        "Context identifiers must be nonblank strings.",
        "Ingrese un ID para el trabajo.",
    ),
    "job_form_paired": (
        "Enter both damage and probability for each measurement.",
        "Ingrese el daño y la probabilidad de cada medición.",
    ),
    "job_form_select_existing": (
        "Select an existing job before deleting.",
        "Seleccione un trabajo existente antes de eliminarlo.",
    ),
    "job_form_history": (
        "This job is referenced by an assessment and cannot be deleted.",
        "Una evaluación hace referencia a este trabajo; no se puede eliminar.",
    ),
    "job_form_complete": (
        "Approval requires at least one complete measurement.",
        "La aprobación requiere al menos una medición completa.",
    ),
    "job_form_changed": (
        "Job details changed since the form was loaded.",
        "Los datos del trabajo cambiaron. Vuelva a cargar el formulario.",
    ),
    "job_form_retry_validation": (
        "Review the form values and try again.",
        "Revise los valores del formulario e inténtelo de nuevo.",
    ),
    "job_tool": ("Tool", "Herramienta"),
    "job_damage_header": ("Total\nCumulative Damage", "Daño acumulado\ntotal"),
    "job_probability_header": (
        "Probability\nOutcome (%)",
        "Probabilidad\ndel resultado (%)",
    ),
    "job_invalid_measurement": (
        "Enter finite nonnegative damage and a probability from 0 to 100.",
        "Ingrese un daño finito no negativo y una probabilidad entre 0 y 100.",
    ),
    "placements_title": (
        "Workplace assignments",
        "Asignaciones de puestos",
    ),
    "placements_window": (
        "{job} Workplace Assignments",
        "{job} · Asignaciones de puestos",
    ),
    "placements_job": (
        "Job: {job}",
        "Trabajo: {job}",
    ),
    "placements_filter": (
        "Filter by plant, section, line, or station",
        "Filtrar por planta, sección, línea o estación",
    ),
    "placements_shift": (
        "Shift",
        "Turno",
    ),
    "placements_shift_tip": (
        "Select the shift whose Job station assignments you want to view or edit.",
        "Seleccione el turno cuyas asignaciones desea ver o editar.",
    ),
    "placements_use": (
        "Use",
        "Usar",
    ),
    "placements_hierarchy": (
        "Workplace hierarchy",
        "Jerarquía de puestos",
    ),
    "placements_level": (
        "Level",
        "Nivel",
    ),
    "placements_tree_tip": (
        "Check any hierarchy level to assign the Job to its stations for "
        "the selected shift.",
        "Marque cualquier nivel para asignar el trabajo a sus estaciones "
        "en el turno seleccionado.",
    ),
    "placements_clear": (
        "Clear shift assignments",
        "Limpiar asignaciones del turno",
    ),
    "placements_clear_tip": (
        "Clear every station assignment for the shift currently displayed.",
        "Quite todas las asignaciones del turno mostrado.",
    ),
    "placements_save": (
        "Save assignments",
        "Guardar asignaciones",
    ),
    "placements_plant": (
        "Plant",
        "Planta",
    ),
    "placements_section": (
        "Section",
        "Sección",
    ),
    "placements_line": (
        "Line",
        "Línea",
    ),
    "placements_station": (
        "Station",
        "Estación",
    ),
    "placements_count": (
        "{current} station(s) selected for shift {shift}; {total} total "
        "workplace assignment(s).",
        "{current} estación(es) en turno {shift}; {total} asignación(es) en total.",
    ),
    "placements_neutral": (
        "Organization-neutral Job: available to JROT without a workplace assignment.",
        "Trabajo sin ubicación: disponible en JROT sin asignación de puesto.",
    ),
    "placements_error_title": (
        "Workplace Assignments",
        "Asignaciones de puestos",
    ),
    "placements_error": (
        "Assignments could not be saved. Your selections are still here. "
        "If project data changed, reopen this dialog before trying again.",
        "No se pudieron guardar las asignaciones. Sus selecciones se "
        "conservan. Si los datos del proyecto cambiaron, vuelva a abrir "
        "este diálogo antes de reintentar.",
    ),
    "new_assessment": (
        "New assessment",
        "Nueva evaluación",
    ),
    "unbound": (
        "No assignment link",
        "Sin vínculo de asignación",
    ),
    "assessment_context": (
        "Assessment context",
        "Contexto de evaluación",
    ),
    "choose_worker": (
        "Select worker",
        "Seleccione trabajador",
    ),
    "discard_changes": (
        "Discard changes",
        "Descartar cambios",
    ),
    "select": (
        "Select",
        "Seleccionar",
    ),
    "look_in": (
        "Look in",
        "Buscar en",
    ),
    "file_name": (
        "File name",
        "Nombre de archivo",
    ),
    "file_type": (
        "File type",
        "Tipo de archivo",
    ),
    "subtitle": (
        "Lifting Fatigue Failure Tool",
        "Herramienta de fatiga por levantamiento",
    ),
    "new": (
        "New",
        "Nuevo",
    ),
    "open": (
        "Open",
        "Abrir",
    ),
    "cancel": (
        "Cancel",
        "Cancelar",
    ),
    "export_csv": ("Export selected tool to CSV", "Exportar herramienta a CSV"),
    "export_empty": (
        "No accepted assessments were found for this tool.",
        "No se encontraron evaluaciones aceptadas de esta herramienta.",
    ),
    "export_done": (
        "Accepted summaries exported. Check status columns; the project was not saved.",
        "Resúmenes aceptados exportados. Revise estados; el proyecto no se guardó.",
    ),
    "save_as": ("Save Project As", "Guardar proyecto como"),
    "backup": ("Backup saved project", "Copia del proyecto guardado"),
    "snapshot_exists": (
        "That destination already exists. Choose a new filename.",
        "Ese destino ya existe. Elija un nombre de archivo nuevo.",
    ),
    "backup_saved": (
        "Saved-project backup created. Unsaved edits were not included.",
        "Copia creada del proyecto guardado. No incluye ediciones sin guardar.",
    ),
    "save": (
        "Save",
        "Guardar",
    ),
    "undo": (
        "Undo",
        "Deshacer",
    ),
    "redo": (
        "Redo",
        "Rehacer",
    ),
    "add": (
        "Add task",
        "Agregar tarea",
    ),
    "remove": (
        "Remove task",
        "Eliminar tarea",
    ),
    "calculate": (
        "Calculate",
        "Calcular",
    ),
    "apply": (
        "Apply edit",
        "Aplicar edición",
    ),
    "discard": (
        "Discard edit",
        "Descartar edición",
    ),
    "task": (
        "Task",
        "Tarea",
    ),
    "lever_arm": (
        "Lever arm",
        "Brazo de palanca",
    ),
    "load": (
        "Load",
        "Carga",
    ),
    "repetitions": (
        "Repetitions / day",
        "Repeticiones / día",
    ),
    "damage": (
        "Cumulative damage",
        "Daño acumulado",
    ),
    "probability": (
        "Probability (%)",
        "Probabilidad (%)",
    ),
    "display": (
        "Display units",
        "Unidades de vista",
    ),
    "decimal": (
        "Decimal separator",
        "Separador decimal",
    ),
    "language": (
        "Language",
        "Idioma",
    ),
    "imperial": (
        "Imperial (in / lbf)",
        "Imperial (in / lbf)",
    ),
    "metric": (
        "Metric (cm / N)",
        "Métrico (cm / N)",
    ),
    "source": (
        "Recorded units",
        "Unidades registradas",
    ),
    "empty": (
        "Create or open a project to begin.",
        "Cree o abra un proyecto para comenzar.",
    ),
    "pending": (
        "Apply or discard the pending edit first.",
        "Aplique o descarte primero la edición pendiente.",
    ),
    "ready": (
        "Select a task and edit one field at a time.",
        "Seleccione una tarea y edite un campo a la vez.",
    ),
    "saved": (
        "Project saved.",
        "Proyecto guardado.",
    ),
    "error": (
        "Operation failed. Your edits are retained.",
        "La operación falló. Se conservaron sus ediciones.",
    ),
    "dirty": (
        "Save project changes before continuing?",
        "¿Guardar los cambios del proyecto antes de continuar?",
    ),
    "pick": (
        "Select assessment",
        "Seleccione evaluación",
    ),
    "convert_project": (
        "Open original project as a converted copy",
        "Abrir proyecto original como copia convertida",
    ),
    "no_assessments": (
        "This project contains no assessment.",
        "Este proyecto no contiene una evaluación.",
    ),
    "no_lifft": (
        "This project contains no LiFFT assessment.",
        "Este proyecto no contiene una evaluación LiFFT.",
    ),
    "development": (
        "Development preview · LiFFT",
        "Vista de desarrollo · LiFFT",
    ),
    "result_units": (
        "Results use recorded units.",
        "Los resultados usan las unidades registradas.",
    ),
    "source_choice": (
        "Recorded units for the new assessment",
        "Unidades registradas para la nueva evaluación",
    ),
}


def desktop_text(key: str, language: Language) -> str:
    """Resolve an explicit message; missing keys fail during development.

    Args:
        key: Stable message/asset/opaque-choice key or typed marker owner, as required
            by the operation; never parsed from a caption.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized caption for the explicit stable key; absent keys fail rather than
        silently hiding missing coverage.

    Raises:
        KeyError: The explicit stable message key is not present in the
            supported-language catalog.
    """
    return _MESSAGES[key][0 if language is Language.ENGLISH else 1]


# Known reference job-form wording mapped to shared stable message keys for
# localization.
_JOB_FORM_KEYS = {
    values[0]: key for key, values in _MESSAGES.items() if key.startswith("job_form_")
}


def job_management_text(source: str, language: Language) -> str:
    """Translate reference form wording without changing stored user evidence.

    English source wording maps to stable shared catalog keys. Unknown framework text is
    retained; arbitrary user-entered values never pass through this map.

    Args:
        source: English reference UI wording or earlier project path, as stated by this
            operation; user values are retained literally.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized known reference wording; unknown framework text is retained literally.
    """
    key = _JOB_FORM_KEYS.get(source)
    return desktop_text(key, language) if key is not None else source


def job_management_error(source: str, language: Language) -> str:
    """Localize known validation messages; use a neutral Spanish fallback otherwise.

    Args:
        source: English reference UI wording or earlier project path, as stated by this
            operation; user values are retained literally.
        language: UI language only; does not reinterpret saved names, numeric inputs or
            units.

    Returns:
        Localized known validation message; unknown Spanish failures use a neutral
        retry/validation message.
    """
    if language is Language.ENGLISH or source in _JOB_FORM_KEYS:
        return job_management_text(source, language)
    if source == desktop_text("job_invalid_measurement", language):
        return source
    return desktop_text("job_form_retry_validation", language)
