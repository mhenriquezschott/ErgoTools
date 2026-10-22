"""Small immutable English/Spanish catalog for migrated risk and draft messages.

Presentation layer. Text/style data has no project I/O; callers supply language and keep
record identities and numeric parsing separate.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ergotools.application.settings import Language as Language

# Immutable English messages indexed by stable keys; scientific and user data are not
# translated.
_ENGLISH: Mapping[str, str] = MappingProxyType(
    {
        "plot.history.filters": "Change filters/tool/view",
        "plot.history.move": "Move/scale marker",
        "plot.history.settings": "Edit marker settings",
        "plot.history.batch": "Edit worker markers",
        "plot.history.cancel": "Cancel marker changes",
        "plot.history.edit_menu": "Edit",
        "plot.history.undo": "Undo",
        "plot.history.redo": "Redo",
        "plot.history.typing": "typing",
        "plot.history.pending_fields": (
            "Save pending coordinates first; typing has its own Undo/Redo."
        ),
        "settings.recent_update_failed": (
            "Document opened, but recent history could not be saved."
        ),
        "project.rotation_draft_incomplete": (
            "Complete the JROT draft or cancel it before saving the project."
        ),
        "project.cleanup_failed": "A previous project connection still needs closing.",
        "review.lifft_metric_moment": (
            "LiFFT metric moment conversion requires review before evaluation."
        ),
        "review.tst_direction": (
            "TST direction labels require review before evaluation."
        ),
        "review.tst_metric_moment": (
            "TST metric moment conversion requires review before evaluation."
        ),
        "edit.tst.add_task": "Add TST task",
        "edit.tst.replace_task": "Edit TST task",
        "edit.tst.remove_task": "Remove TST task",
        "risk.low": "Low Risk",
        "risk.moderate": "Moderate Risk",
        "risk.moderate_high": "Moderate High Risk",
        "risk.high": "High Risk",
        "edit.lifft.add_task": "Add LiFFT task",
        "edit.lifft.task_count": "Set LiFFT task count",
        "edit.duet.task_count": "Set DUET task count",
        "edit.tst.task_count": "Set ST task count",
        "edit.duet.add_task": "Add DUET task",
        "edit.duet.replace_task": "Edit DUET task",
        "edit.duet.remove_task": "Remove DUET task",
        "edit.lifft.replace_task": "Edit LiFFT task",
        "edit.lifft.remove_task": "Remove LiFFT task",
        "validation.number": "Enter a valid number.",
        "validation.tst_direction": "Select a supported shoulder-task direction.",
        "validation.omni_scale": "Select an integer OMNI-Res rating from 0 to 10.",
        "validation.nonnegative": "Enter a nonnegative value.",
        "validation.overflow": "The calculation exceeds the supported numeric range.",
        "validation.required": "A value is required.",
        "evaluation.lifft_incomplete": (
            "Warning: Incomplete input - results include completed rows only."
        ),
        "validation.tasks_required": "Add at least one task before calculating.",
        "validation.nonfinite": "Enter a finite number.",
        "validation.unit": "Unsupported measurement system.",
        "validation.duplicate": "Task identity already exists.",
        "validation.missing_task": "The task no longer exists.",
        "validation.stale_task": "The task has changed. Reload it before editing.",
        "validation.stale_editor": (
            "The editor context has changed. Refresh before submitting this value."
        ),
        "validation.stale_view": "The source has changed. Refresh before editing.",
        "validation.position": "Invalid task position.",
        "validation.identity": "Task identity cannot change.",
    }
)
# Spanish owned interface wording; unknown English captions retain the documented
# fallback.
_SPANISH: Mapping[str, str] = MappingProxyType(
    {
        "plot.history.filters": "Cambiar filtros/herramienta/vista",
        "plot.history.move": "Mover/escalar marcador",
        "plot.history.settings": "Editar ajustes del marcador",
        "plot.history.batch": "Editar marcadores de trabajadores",
        "plot.history.cancel": "Cancelar cambios del marcador",
        "plot.history.edit_menu": "Editar",
        "plot.history.undo": "Deshacer",
        "plot.history.redo": "Rehacer",
        "plot.history.typing": "escritura",
        "plot.history.pending_fields": (
            "Guarde primero las coordenadas pendientes; "
            "la escritura tiene su propio Deshacer/Rehacer."
        ),
        "settings.recent_update_failed": (
            "El documento se abrió, pero no se pudo guardar el historial reciente."
        ),
        "project.rotation_draft_incomplete": (
            "Complete el borrador de JROT o cancélelo antes de guardar el proyecto."
        ),
        "project.cleanup_failed": "Aún falta cerrar una conexión de proyecto anterior.",
        "review.lifft_metric_moment": (
            "La conversión del momento métrico de LiFFT requiere revisión "
            "antes de evaluar."
        ),
        "review.tst_direction": (
            "Las etiquetas de dirección de TST requieren revisión antes de evaluar."
        ),
        "review.tst_metric_moment": (
            "La conversión del momento métrico de TST requiere revisión "
            "antes de evaluar."
        ),
        "edit.tst.add_task": "Agregar tarea TST",
        "edit.tst.replace_task": "Editar tarea TST",
        "edit.tst.remove_task": "Eliminar tarea TST",
        "risk.low": "Riesgo bajo",
        "risk.moderate": "Riesgo moderado",
        "risk.moderate_high": "Riesgo moderado alto",
        "risk.high": "Riesgo alto",
        "edit.lifft.add_task": "Agregar tarea LiFFT",
        "edit.lifft.task_count": "Establecer número de tareas LiFFT",
        "edit.duet.task_count": "Establecer número de tareas DUET",
        "edit.tst.task_count": "Establecer número de tareas ST",
        "edit.duet.add_task": "Agregar tarea DUET",
        "edit.duet.replace_task": "Editar tarea DUET",
        "edit.duet.remove_task": "Eliminar tarea DUET",
        "edit.lifft.replace_task": "Editar tarea LiFFT",
        "edit.lifft.remove_task": "Eliminar tarea LiFFT",
        "validation.number": "Ingrese un número válido.",
        "validation.tst_direction": (
            "Seleccione una dirección de tarea de hombro válida."
        ),
        "validation.omni_scale": "Seleccione una escala OMNI-Res entera de 0 a 10.",
        "validation.nonnegative": "Ingrese un valor no negativo.",
        "validation.overflow": "El cálculo excede el rango numérico admitido.",
        "validation.required": "Se requiere un valor.",
        "evaluation.lifft_incomplete": (
            "Advertencia: Entrada incompleta - "
            "los resultados incluyen solo filas completas."
        ),
        "validation.tasks_required": "Agregue al menos una tarea antes de calcular.",
        "validation.nonfinite": "Ingrese un número finito.",
        "validation.unit": "Sistema de unidades no admitido.",
        "validation.duplicate": "La identidad de la tarea ya existe.",
        "validation.missing_task": "La tarea ya no existe.",
        "validation.stale_task": (
            "La tarea ha cambiado. Vuelva a cargarla antes de editar."
        ),
        "validation.stale_editor": (
            "El contexto de edición cambió. Actualice antes de enviar este valor."
        ),
        "validation.stale_view": (
            "Los datos han cambiado. Actualice la vista antes de editar."
        ),
        "validation.position": "Posición de tarea no válida.",
        "validation.identity": "La identidad de la tarea no puede cambiar.",
    }
)
# Supported immutable catalogs keyed by Language; completeness is checked independently
# of global locale.
_CATALOGS: Mapping[Language, Mapping[str, str]] = MappingProxyType(
    {
        Language.ENGLISH: _ENGLISH,
        Language.SPANISH: _SPANISH,
    }
)


@dataclass(frozen=True, slots=True)
class Translator:
    """Per-view language context with no global locale or application mutation.

    Attributes:
        language: Supported per-view language; no global process locale is changed.
    """

    language: Language = Language.ENGLISH

    def __post_init__(self) -> None:
        """Reject unsupported languages instead of silently displaying another.

        Args:
            None.

        Returns:
            None.

        Raises:
            ValueError: The supplied ownership, enum or value violates the operation's
                validated contract.
        """
        if self.language not in _CATALOGS:
            raise ValueError(f"Unsupported language: {self.language}")

    @property
    def keys(self) -> frozenset[str]:
        """Expose keys for catalog completeness checks without mutable access.

        Args:
            None.

        Returns:
            Immutable supported translation-key set for completeness checks; no mutable
            catalog access is exposed.
        """
        return frozenset(_CATALOGS[self.language])

    def text(self, key: str) -> str:
        """Resolve a stable message key; raise KeyError for missing translations.

        Missing translations fail explicitly during development. There is no fallback to
        English that could conceal incomplete catalog migration. This initial catalog
        does not handle pluralization or numeric parsing.

        Args:
            key: Stable message/asset/opaque-choice key or typed marker owner, as
                required by the operation; never parsed from a caption.

        Returns:
            Exact supported-language catalog message for the stable key; there is no
            silent fallback.

        Raises:
            KeyError: The explicit stable message key is not present in the
                supported-language catalog.
        """
        return _CATALOGS[self.language][key]
