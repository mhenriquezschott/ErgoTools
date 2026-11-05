"""Recalculate earlier native projects into a single-result native container.

External tools layer only. Current saved inputs/catalogs are read from a private SQLite
backup, all prior result/archive tables are discarded, and the established application
evaluator builds one result per assessment. Format-14/15/16/17/18 results stay exact;
owner-rejected Shift/Station attributes and the redundant Plant shift count are
removed before strict date/duration validation.
Original input files stay unchanged.
No archived result is decoded or carried into the output.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from ergotools.application.saved_results import calculate_saved_result
from ergotools.application.session import DocumentKey
from ergotools.infrastructure.assessment_project_file import AssessmentProjectFile
from ergotools.infrastructure.draft_json import (
    document_fields,
    document_text,
    unique_object,
)
from ergotools.infrastructure.project_snapshot import (
    ProjectSnapshot,
    SnapshotAssessment,
)
from ergotools.infrastructure.rotation_scenario_serialization import is_scenario_payload
from ergotools.infrastructure.rotation_timing_store import create_rotation_timing_schema
from ergotools.infrastructure.task_catalog_store import create_task_schema
from ergotools.infrastructure.work_hierarchy_store import decode_hierarchy

from .job_risk_upgrade import upgrade_job_risks
from .ownership_upgrade import upgrade_assessment_ownership

# Explicit owner-removed fields by entity; these names are conversion input only.
_REMOVED_ORGANIZATION_FIELDS: dict[str, tuple[str, ...]] = {
    "Shift": ("incidents_reported", "ergonomic_risk_events"),
    "Station": (
        "task_description",
        "equipment_used",
        "ergonomic_risk_level",
        "performance_metric",
        "power_consumption",
        "materials_used",
    ),
    "Plant": ("number_of_shifts",),
}


def upgrade_previous_project(source: Path, destination: Path) -> AssessmentProjectFile:
    """Upgrade an earlier native project to a separate current-format copy.

    Formats 8-13 remove obsolete duplicate results in private memory and recalculate
    older rounded outputs using unchanged formulas, units and direction conventions.
    Formats 14-23 retain authoritative native results exactly. Modern marker upgrades
    preserve supported payload bytes, fingerprints and timestamps.

    Args:
        source: Existing full native format 8-23 project, opened read-only.
        destination: Nonexistent output path; never replaces an original project.

    Returns:
        Owned open format-24 repository containing current catalogs, every plant
        image/scheme/source and one complete/partial calculation per evaluable
        assessment.
        Invalid calculations have no fabricated output. Caller must close it.

    Raises:
        ValueError: Input format or native relationships are invalid.
        OSError: Input or exclusive publication fails.
        sqlite3.Error: Native data or snapshot operations are invalid.
        FileExistsError: The separate destination already exists; never overwrite it.
    """
    if destination.exists():
        raise FileExistsError(destination)
    with (
        closing(
            sqlite3.connect(source.absolute().as_uri() + "?mode=ro", uri=True)
        ) as original,
        closing(sqlite3.connect(":memory:")) as working,
    ):
        original.backup(working)
        row = working.execute("SELECT version FROM project_metadata").fetchone()
        if row is None or row[0] not in (
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
        ):
            raise ValueError("Only earlier full native formats 8-23 need this upgrade.")
        version = row[0]
        if 11 <= version < 22 and any(
            is_scenario_payload(record[0])
            for record in working.execute("SELECT payload FROM rotation_schemes")
        ):
            raise ValueError(
                "Guided rotation payloads require the current native marker."
            )
        if version in (22, 23):
            # Validate the source capability marker before advancing it; never hide
            # unsupported drafts or malformed current ownership behind a newer marker.
            probe = sqlite3.connect(":memory:")
            try:
                working.backup(probe)
                with AssessmentProjectFile(probe):
                    pass
            finally:
                probe.close()
        with working:
            working.execute("BEGIN IMMEDIATE")
            remove_obsolete_organization_fields(working)
            upgrade_assessment_ownership(working)
            upgrade_job_risks(working)
            for table in (
                "legacy_source_images",
                "legacy_source_evidence",
                "recorded_assessment_results",
            ):
                # Constant allow-list, not user-supplied SQL identifiers.
                working.execute(f"DROP TABLE IF EXISTS {table}")
            if version not in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
                working.execute("DROP TABLE IF EXISTS saved_assessment_results")
            if version in (12, 13):
                working.execute("UPDATE project_metadata SET version=11")
            elif version in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
                if version < 20:
                    create_task_schema(working)
                if version < 21:
                    create_rotation_timing_schema(working)
                working.execute("UPDATE project_metadata SET version=24")
        if version in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23):
            return _publish_native_upgrade(working, destination)
        with AssessmentProjectFile(working) as native:
            metadata = native.metadata
            ownership = native.load_history().entries
            assessments = tuple(
                SnapshotAssessment(
                    item,
                    native.load(DocumentKey(metadata.project_id, item.document_id)),
                )
                for item in ownership
            )
            results = tuple(
                (item.ownership.document_id, result)
                for item in assessments
                if (
                    result := (
                        native.load_saved_result(
                            DocumentKey(metadata.project_id, item.ownership.document_id)
                        )
                        if version in (14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
                        else calculate_saved_result(
                            DocumentKey(
                                metadata.project_id, item.ownership.document_id
                            ),
                            item.source,
                            metadata.default_units,
                        )
                    )
                )
                is not None
            )
            hierarchy = native.load_hierarchy()
            images = tuple(
                (plant, image)
                for plant in hierarchy.plants
                if (image := native.load_plant_image(plant)) is not None
            )
            snapshot = ProjectSnapshot(
                metadata,
                hierarchy,
                native.load_jobs(),
                native.load_job_risk(),
                assessments,
                images,
                native.load_plot_positions(),
                native.load_rotation_schemes(),
                results,
            )
        return AssessmentProjectFile.create_from_snapshot(destination, snapshot)


def _publish_native_upgrade(
    connection: sqlite3.Connection, destination: Path
) -> AssessmentProjectFile:
    """Validate and publish the private native upgrade without rewriting other data.

    Args:
        connection: Idle private in-memory conversion copy with format-24 metadata.
        destination: Nonexistent owner-selected output path; never replaces the source.

    Returns:
        Owned repository reopened from the exclusively published output. Exact image,
        task/result, scheme payload and creation/update timestamp bytes are retained.

    Raises:
        ValueError: The converted ownership/source/result relationships are invalid.
        OSError: Temporary storage, publication or cleanup fails; no overwrite fallback.
        FileExistsError: Destination exists or is created by a competing publication.
        sqlite3.Error: Backup or repository validation fails before publication.
    """
    descriptor, filename = tempfile.mkstemp(
        prefix=".ergotools-native-upgrade-", suffix=".sqlite", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(filename)
    try:
        with closing(sqlite3.connect(temporary)) as staging:
            connection.backup(staging)
        with AssessmentProjectFile.open(temporary) as candidate:
            candidate.load_history()
            candidate.load_plot_positions().validate(
                candidate.load_hierarchy(), candidate.load_jobs()
            )
            candidate.load_rotation_schemes()
            for entry in candidate.list_assessments():
                candidate.load_saved_result(entry.document)
        os.link(temporary, destination)
        return AssessmentProjectFile.open(destination)
    finally:
        temporary.unlink(missing_ok=True)


def remove_obsolete_organization_fields(connection: sqlite3.Connection) -> int:
    """Remove obsolete organization attributes under explicit owner correction.

    This external conversion step runs before native validation. Other attributes,
    identities and tables remain untouched. The current codec validates the complete
    filtered catalog before its single write; unknown fields still fail conversion.

    Args:
        connection: Private conversion copy inside a caller-owned transaction. The
            caller owns rollback and publication, never an original operational file.

    Returns:
        Number of removed attribute pairs, including empty values and the retired
        editable Plant shift count. Populated values
        are intentionally removed under the owner's explicit field-removal decision.

    Raises:
        RuntimeError: The caller has not started a conversion transaction.
        ValueError: Catalog shape or remaining domain metadata is invalid.
        sqlite3.Error: Catalog reading or transactional replacement fails.
    """
    if not connection.in_transaction:
        raise RuntimeError(
            "Organization field removal requires a conversion transaction."
        )
    row = connection.execute("SELECT payload FROM work_catalog").fetchone()
    if row is None:
        raise ValueError("Missing organization catalog.")
    envelope = document_fields(
        json.loads(row[0], object_pairs_hook=unique_object), {"version", "hierarchy"}
    )
    hierarchy = envelope["hierarchy"]
    if not isinstance(hierarchy, dict):
        raise ValueError("Invalid organization hierarchy.")
    organization = hierarchy.get("organization", [])
    if not isinstance(organization, list):
        raise ValueError("Invalid organization records.")
    removed = 0
    for item in organization:
        record = document_fields(item, {"kind", "keys", "attributes"})
        attributes = record["attributes"]
        if not isinstance(attributes, list):
            raise ValueError("Invalid organization attributes.")
        retained = []
        for pair in attributes:
            if not isinstance(pair, list) or len(pair) != 2:
                raise ValueError("Invalid organization attribute pair.")
            if pair[0] in _REMOVED_ORGANIZATION_FIELDS.get(
                document_text(record["kind"]), ()
            ):
                removed += 1
            else:
                retained.append(pair)
        item["attributes"] = retained
    payload = json.dumps(
        envelope, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    decode_hierarchy(payload)
    if removed:
        connection.execute(
            "UPDATE work_catalog SET payload=? WHERE singleton=1", (payload,)
        )
    return removed
