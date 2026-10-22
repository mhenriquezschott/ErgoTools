"""Saved JROT arrangements adapted to current Job values during conversion.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from dataclasses import dataclass, replace

from ergotools.domain.assessments.context import WorkplaceContext
from ergotools.domain.rotation import WorkerRotation
from ergotools.domain.rotation_scheme import (
    RotationMode,
    RotationScheme,
    RotationTarget,
    RotationWorkerLink,
)

from .legacy_catalogs import LegacyCatalogs
from .legacy_project import LegacyProject, LegacyRow
from .legacy_values import (
    legacy_integer,
    legacy_keys,
    legacy_kind,
    legacy_text,
    optional_integer,
    optional_text,
)

# ASCII-only translation matching SQLite NOCASE for original worker/scheme ordering.
_ASCII_FOLD = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


@dataclass(frozen=True, slots=True)
class LegacyRotations:
    """Validated schemes and raw records/timestamps for conversion evidence.

    Attributes:
        schemes: Validated arrangements with exact Job/placement and worker links.
        original_schemes: Original scheme rows, including source timestamps, for
            conversion inspection.
        original_scopes: Original scheme-to-workplace scope rows.
        original_targets: Original scheme target rows whose IDs map to opaque native
            target keys.
        original_assignments: Original worker/block/target rows, including original
            assignment links.
    """

    schemes: tuple[RotationScheme, ...]
    original_schemes: tuple[LegacyRow, ...]
    original_scopes: tuple[LegacyRow, ...]
    original_targets: tuple[LegacyRow, ...]
    original_assignments: tuple[LegacyRow, ...]


def _groups(rows: tuple[LegacyRow, ...]) -> dict[str, list[LegacyRow]]:
    """Group rotation child rows by exact scheme identity.

    Args:
        rows: Original rotation child records in caller-supplied order, each with a
            scheme_id.

    Returns:
        Mutable grouping dictionary whose lists preserve each input scheme's child-row
        order.

    Raises:
        KeyError: An original child row lacks scheme_id.
        ValueError: An original scheme identity is not text.
    """
    groups: dict[str, list[LegacyRow]] = {}
    for row in rows:
        groups.setdefault(legacy_text(row["scheme_id"]), []).append(row)
    return groups


def read_legacy_rotations(
    project: LegacyProject, catalogs: LegacyCatalogs
) -> LegacyRotations:
    """Read saved shape/scope/provenance with exact original historical references.

    Remove old profile references while keeping Job/placement and worker arrangements.
    If a saved target used another profile, invalidate optimization provenance.
    Original target row IDs map to opaque typed target keys. Worker
    ordering matches SQLite NOCASE's ASCII folding; blocks stay zero based. No solve,
    save, schema migration or missing-cell repair occurs.

    Args:
        project: Caller-owned open read-only version-eight snapshot; this operation does
            not close it.
        catalogs: Validated source hierarchy/jobs/risks preserving exact original
            historical identities.

    Returns:
        Validated typed schemes with frozen historical links plus read-only original
        rows for conversion checks.

    Raises:
        ValueError: Inconsistent dimensions, links, scope or optimization provenance.
        KeyError: Required source schema/catalog records are missing.
    """
    contexts = {
        legacy_integer(row["id"]): WorkplaceContext(
            *legacy_keys(
                row, "plant_name", "section_name", "line_name", "station_id", "shift_id"
            )
        )
        for row in project.rows("WorkplaceContext")
    }
    raw_schemes = tuple(
        sorted(
            project.rows("RotationScheme"),
            key=lambda row: legacy_text(row["id"]).translate(_ASCII_FOLD),
        )
    )
    raw_scopes = project.rows(
        "RotationSchemeScope", order=("scheme_id", "workplace_context_id")
    )
    raw_targets = project.rows("RotationTarget", order=("id",))
    raw_assignments = project.rows(
        "RotationAssignment", order=("scheme_id", "block_index", "worker_id")
    )
    scopes, targets, assignments = (
        _groups(rows) for rows in (raw_scopes, raw_targets, raw_assignments)
    )
    profiles = {
        legacy_integer(row["id"]): row for row in project.rows("JobRiskProfile")
    }
    selected_profiles = {
        legacy_text(row["job_id"]): legacy_integer(row["id"])
        for row in profiles.values()
        if row["is_current"] == 1
    }
    result = []
    for row in raw_schemes:
        identity = legacy_text(row["id"])
        blocks = legacy_integer(row["num_timeblocks"])
        count = legacy_integer(row["num_workers"])
        if blocks <= 0 or count <= 0:
            raise ValueError("Legacy rotation dimensions must be positive.")
        selected_targets = tuple(
            sorted(
                targets.pop(identity, ()),
                key=lambda t: (
                    legacy_text(t["job_id"]).translate(_ASCII_FOLD),
                    legacy_integer(t["id"]),
                ),
            )
        )
        changed_risks = False
        for original_target in selected_targets:
            profile_id = legacy_integer(original_target["job_risk_profile_id"])
            job_id = legacy_text(original_target["job_id"])
            if profile_id not in profiles or profiles[profile_id]["job_id"] != job_id:
                raise ValueError("Rotation target references another Job's risks.")
            if selected_profiles.get(job_id) != profile_id:
                changed_risks = True
        typed_targets = tuple(
            RotationTarget(
                legacy_text(target["job_id"]),
                optional_integer(target["job_placement_id"]),
            )
            for target in selected_targets
        )
        target_keys = {
            legacy_integer(target["id"]): typed.key
            for target, typed in zip(selected_targets, typed_targets, strict=True)
        }
        by_worker: dict[str, dict[int, str]] = {}
        links: dict[str, int | None] = {}
        for assignment in assignments.pop(identity, ()):
            worker = legacy_text(assignment["worker_id"])
            owner = optional_integer(assignment["worker_assignment_id"])
            if worker in links and links[worker] != owner:
                raise ValueError("Rotation worker assignment differs across blocks.")
            links[worker] = owner
            target = legacy_integer(assignment["rotation_target_id"])
            block = legacy_integer(assignment["block_index"])
            if target not in target_keys or block in by_worker.setdefault(worker, {}):
                raise ValueError("Rotation cell has an ambiguous or foreign target.")
            by_worker[worker][block] = target_keys[target]
        if len(by_worker) != count or any(
            set(cells) != set(range(blocks)) for cells in by_worker.values()
        ):
            raise ValueError("Legacy rotation does not fill its declared grid.")
        workers = tuple(
            sorted(by_worker, key=lambda worker: worker.translate(_ASCII_FOLD))
        )
        primary = optional_text(row["primary_tool_id"])
        scheme = RotationScheme(
            catalogs.jobs.project_id,
            identity,
            legacy_text(row["name"]),
            tuple(RotationWorkerLink(worker, links[worker]) for worker in workers),
            typed_targets,
            tuple(
                WorkerRotation(
                    worker, tuple(by_worker[worker][block] for block in range(blocks))
                )
                for worker in workers
            ),
            tuple(
                contexts[legacy_integer(scope["workplace_context_id"])]
                for scope in scopes.pop(identity, ())
            ),
            RotationMode(legacy_text(row["optimization_mode"])),
            legacy_kind(primary) if primary is not None else None,
            optional_text(row["description"]),
        )
        if changed_risks and scheme.mode is not RotationMode.MANUAL:
            scheme = replace(scheme, mode=RotationMode.MANUAL, primary_kind=None)
        scheme.validate_references(catalogs.hierarchy, catalogs.jobs, catalogs.risks)
        result.append(scheme)
    if scopes or targets or assignments:
        raise ValueError("Rotation child records have no original scheme.")
    return LegacyRotations(
        tuple(result), raw_schemes, raw_scopes, raw_targets, raw_assignments
    )
