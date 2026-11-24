"""Tablet organization/timing commands over unchanged native application contracts.

No SQL, schema extension or calculator logic. Every mutation uses explicit expected
state, native guarded transactions and the host's common project history/Save.
"""

from pathlib import Path

from ergotools.application.organization_management import (
    delete_organization,
    save_organization,
)
from ergotools.application.rotation_timing import shift_clock
from ergotools.domain.organization_record import (
    ORGANIZATION_FIELDS,
    OrganizationKind,
    OrganizationRecord,
)
from ergotools.domain.rotation_timing import RotationTiming
from ergotools.domain.work_hierarchy import WorkHierarchy
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile


def organization_snapshot(path: Path) -> tuple:
    """Detach hierarchy and reusable shift timings without manufacturing defaults.

    Args:
        path: Current private native project.

    Returns:
        Exact hierarchy and immutable timing templates.
    """
    with AssessmentProjectFile.open(path) as project:
        return project.load_hierarchy(), project.load_shift_timings()


def record_from_form(
    original: OrganizationRecord, identifier: str, values: dict[str, str]
) -> OrganizationRecord:
    """Parse accepted fields while preserving untouched optional metadata exactly.

    Args:
        original: Exact record shown by the form, including explicit empty/null values.
        identifier: Proposed last key; hierarchy guards validate creation.
        values: Displayed strings for known fields; blank changed fields clear values.

    Returns:
        Typed record retaining unchanged field order, numeric precision and null/empty
        distinctions. No I/O or inferred clock defaults are introduced.

    Raises:
        ValueError: Unknown field, invalid numeric value or failed domain check.
    """
    kinds = dict(ORGANIZATION_FIELDS[original.kind.value])
    attributes = dict(original.attributes)
    for key, text in values.items():
        if key not in kinds:
            raise ValueError("Unknown organization field.")
        previous = attributes.get(key)
        old_text = "" if previous is None else str(previous)
        current = text.strip()
        if current == old_text:
            continue
        if not current:
            attributes.pop(key, None)
        else:
            attributes[key] = float(current) if kinds[key] == "number" else current
    return OrganizationRecord(
        original.kind,
        (*original.keys[:-1], identifier.strip()),
        tuple(attributes.items()),
    )


def accept_record(
    path: Path,
    expected: WorkHierarchy,
    record: OrganizationRecord,
    *,
    creating: bool,
    reset_timing: bool = False,
) -> None:
    """Apply one hierarchy/metadata edit with explicit incompatible-timing consent.

    Args:
        path: Private native destination, never an external opened source.
        expected: Complete hierarchy shown by the form; stale forms reject.
        record: Validated identity and descriptive fields.
        creating: True creates a new identity; False preserves an existing identity.
        reset_timing: Explicit permission to clear an incompatible shift template.

    Returns:
        None; compatible templates, worker sources and saved results stay exact.

    Raises:
        ValueError: Stale state, invalid hierarchy or unconfirmed incompatible timing.
    """
    replacement = save_organization(expected, record, creating=creating)
    with AssessmentProjectFile.open(path) as project:
        if project.load_hierarchy() != expected:
            raise ValueError("Organization changed. Reopen this form before applying.")
        template = next(
            (
                t
                for t in project.load_shift_timings()
                if record.kind is OrganizationKind.SHIFT
                and t.shift_id == record.keys[0]
            ),
            None,
        )
        incompatible = False
        if template is not None:
            try:
                duration = shift_clock(replacement, record.keys[0]).span_minutes
            except ValueError:
                # Missing optional clocks also invalidate a prior reusable template.
                incompatible = True
            else:
                incompatible = template.timing.shift_minutes != duration
        if incompatible and not reset_timing:
            raise ValueError(
                "The new duration differs from this shift's "
                "timing. Confirm resetting its timing first."
            )
        project.begin_editing(lambda label: None)
        if incompatible:
            project.replace_shift_timing(record.keys[0], template.timing, None)
        project.replace_hierarchy(expected, replacement)
        project.commit_editing()


def remove_record(
    path: Path, expected: WorkHierarchy, kind: OrganizationKind, keys: tuple[str, ...]
) -> None:
    """Delete an exact unreferenced subtree, leaving native reference guards in charge.

    Args:
        path: Current private native file.
        expected: Exact form hierarchy.
        kind: Selected location level or independent shift.
        keys: Complete scoped identity.

    Returns:
        None; referenced assignments/Jobs/assessments prevent removal atomically.

    Raises:
        ValueError: Stale hierarchy or protected references prevent removal.
    """
    with AssessmentProjectFile.open(path) as project:
        if project.load_hierarchy() != expected:
            raise ValueError("Organization changed. Refresh before deleting.")
        replacement = delete_organization(expected, kind, keys)
        project.begin_editing(lambda label: None)
        project.replace_hierarchy(expected, replacement)
        project.commit_editing()


def accept_timing(
    path: Path,
    shift_id: str,
    expected: RotationTiming | None,
    replacement: RotationTiming | None,
) -> None:
    """Commit one expected-value guarded shift timing through the native capability.

    Args:
        path: Current private native file.
        shift_id: Existing independent shift owner.
        expected: Exact prior saved timing or None when absent.
        replacement: Complete proposed template, or None after explicit clear.

    Returns:
        None; the common project Save owns final publication to a saved tablet copy.
    """
    with AssessmentProjectFile.open(path) as project:
        project.begin_editing(lambda label: None)
        project.replace_shift_timing(shift_id, expected, replacement)
        project.commit_editing()
