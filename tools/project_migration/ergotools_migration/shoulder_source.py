"""Translate recorded shoulder selectors into the native explicit convention.

External converter responsibility only: preserve visible choices, missing data and the
original executed branch mapping. No calculation or unit conversion is performed here,
and the desktop never imports this module.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from ergotools.domain.assessments.tst import TstDirection, TstTask
from ergotools.domain.assessments.tst_draft import TstDirectionConvention, TstDraft

from .legacy_assessments import LegacyShoulderSource


def convert_shoulder_source(source: LegacyShoulderSource) -> TstDraft:
    """Retain original dropdown choices with their explicit calculator convention.

    Original files retain raw selector evidence. The converter evaluates the returned
    source separately and writes only that calculation into native storage. No
    calculation or scientific correction is performed inside this mapper.

    Args:
        source: Original selector-index tasks with their declared metric/imperial units.

    Returns:
        Native shoulder source with the original visible choices and REFERENCE_UI branch
        convention. Missing choices remain absent; quantities are unchanged.

    Raises:
        ValueError: A raw selector is unsupported or the resulting draft
            convention/identities are invalid.
    """
    return TstDraft(
        source.system,
        tuple(
            TstTask(
                task.task_id,
                None
                if task.selector_index is None
                else TstDirection(str(task.selector_index)),
                task.lever_arm,
                task.load,
                task.repetitions,
            )
            for task in source.tasks
        ),
        TstDirectionConvention.REFERENCE_UI,
    )
