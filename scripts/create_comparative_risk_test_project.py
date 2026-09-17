#!/usr/bin/env python3
"""Build the committed PLOT individual-versus-Job comparison fixture."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import xml.etree.ElementTree as ET
from itertools import cycle
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC = REPOSITORY_ROOT / "src"
sys.path.insert(0, str(SRC))

from database import connect_database
from schema_migrations import LATEST_SCHEMA_VERSION, migrate_database


DEFAULT_SOURCE = REPOSITORY_ROOT / "tests" / "ErgoTools_IntegratedTest.ergprj"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "tests" / "ErgoTools_ComparativeRiskTest.ergprj"
PROJECT_NAME = "ErgoTools Comparative Individual and Job Risk Test"
FIXTURE_JOBS = tuple(f"Job-S{number:03d}" for number in range(1, 11))
UNPOSITIONED_STATION = (
    "Default", "ThirdSection", "ThirdSectionLine3", "ThirdSectionLine3St1"
)


def project_paths(project_file: Path) -> tuple[ET.ElementTree, Path, Path]:
    tree = ET.parse(project_file)
    root = tree.getroot()
    database = project_file.parent / root.findtext("DataPath") / root.findtext("DatabaseName")
    images = project_file.parent / root.findtext("ImagesPath")
    return tree, database, images


def replace_output(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def active_assessment_contexts(connection: sqlite3.Connection) -> list[int]:
    return [
        int(row[0])
        for row in connection.execute(
            """
            SELECT DISTINCT assignment.workplace_context_id
            FROM IndividualAssessment AS assessment
            JOIN WorkerAssignment AS assignment
              ON assignment.id = assessment.worker_assignment_id
            WHERE assessment.is_current = 1 AND assignment.active = 1
            ORDER BY assignment.workplace_context_id
            """
        )
    ]


def placement_for_context(
    connection: sqlite3.Connection,
    job_id: str,
    context_id: int,
) -> int:
    existing = connection.execute(
        """
        SELECT id FROM JobPlacement
        WHERE job_id = ? AND workplace_context_id = ?
        ORDER BY id LIMIT 1
        """,
        (job_id, context_id),
    ).fetchone()
    if existing is not None:
        placement_id = int(existing[0])
        connection.execute(
            """
            UPDATE JobPlacement
            SET active = 1, notes = 'Comparative-risk development fixture.'
            WHERE id = ?
            """,
            (placement_id,),
        )
        return placement_id
    return int(
        connection.execute(
            """
            INSERT INTO JobPlacement (
                job_id, workplace_context_id, active, notes
            ) VALUES (?, ?, 1, 'Comparative-risk development fixture.')
            """,
            (job_id, context_id),
        ).lastrowid
    )


def configure_database(database: Path, images_folder_name: str) -> dict[str, object]:
    migrate_database(database, create_backup=False)
    with connect_database(database) as connection:
        connection.execute("UPDATE WorkerAssignment SET job_placement_id = NULL")
        connection.execute("UPDATE JobPlacement SET active = 0")

        job_count = connection.execute(
            f"SELECT COUNT(*) FROM Job WHERE id IN ({','.join('?' for _ in FIXTURE_JOBS)})",
            FIXTURE_JOBS,
        ).fetchone()[0]
        if job_count != len(FIXTURE_JOBS):
            raise RuntimeError("The integrated fixture does not contain the expected ten Jobs.")

        contexts = active_assessment_contexts(connection)
        placements = {}
        for context_id, job_id in zip(contexts, cycle(FIXTURE_JOBS)):
            placement_id = placement_for_context(connection, job_id, context_id)
            placements[context_id] = placement_id
            connection.execute(
                """
                UPDATE WorkerAssignment
                SET job_placement_id = ?,
                    notes = 'Classified for comparative-risk development testing.'
                WHERE workplace_context_id = ? AND active = 1
                """,
                (placement_id, context_id),
            )

        # Exercise the valid missing-profile state in Job and Comparison views.
        connection.execute(
            """
            DELETE FROM JobRiskMeasurement
            WHERE tool_id = 'ST' AND profile_id = (
                SELECT id FROM JobRiskProfile
                WHERE job_id = 'Job-S010' AND status = 'approved' AND is_current = 1
            )
            """
        )

        # Exercise the square marker used when sex/gender is not provided.
        square_worker = connection.execute(
            """
            SELECT assignment.worker_id
            FROM WorkerAssignment AS assignment
            JOIN IndividualAssessment AS assessment
              ON assessment.worker_assignment_id = assignment.id
            WHERE assignment.active = 1 AND assessment.is_current = 1
            ORDER BY assignment.worker_id DESC
            LIMIT 1
            """
        ).fetchone()[0]
        connection.execute(
            "UPDATE Worker SET gender = NULL WHERE id = ?",
            (square_worker,),
        )

        connection.execute(
            """
            DELETE FROM PlotStationPosition
            WHERE plant_name = ? AND section_name = ?
              AND line_name = ? AND station_id = ?
            """,
            UNPOSITIONED_STATION,
        )
        connection.execute(
            """
            UPDATE Plant
            SET image_path = ? || '/' || image_name
            WHERE image_name IS NOT NULL AND image_name <> ''
            """,
            (images_folder_name,),
        )

        unclassified = connection.execute(
            """
            SELECT COUNT(*)
            FROM IndividualAssessment AS assessment
            JOIN WorkerAssignment AS assignment
              ON assignment.id = assessment.worker_assignment_id
            WHERE assessment.is_current = 1 AND assignment.active = 1
              AND assignment.job_placement_id IS NULL
            """
        ).fetchone()[0]
        if unclassified:
            raise RuntimeError(f"{unclassified} current assessments remain unclassified.")
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key violations in generated fixture: {violations}")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version != LATEST_SCHEMA_VERSION:
            raise RuntimeError(f"Generated fixture has schema version {version}.")

        return {
            "contexts": len(contexts),
            "placements": len(placements),
            "assessments": connection.execute(
                "SELECT COUNT(*) FROM IndividualAssessment WHERE is_current = 1"
            ).fetchone()[0],
            "square_worker": square_worker,
        }


def build_project(source: Path, output: Path, *, force: bool = False) -> dict[str, object]:
    source = source.resolve()
    output = output.resolve()
    source_tree, source_database, source_images = project_paths(source)
    stem = output.stem
    data_name = f"{stem}_data"
    images_name = f"{stem}_images"
    database_name = f"{stem}_data.db"
    data_folder = output.parent / data_name
    images_folder = output.parent / images_name

    if any(path.exists() for path in (output, data_folder, images_folder)):
        if not force:
            raise FileExistsError("Output fixture already exists; pass --force to rebuild it.")
        for path in (output, data_folder, images_folder):
            replace_output(path)

    data_folder.mkdir(parents=True)
    shutil.copytree(source_images, images_folder)
    database = data_folder / database_name
    shutil.copy2(source_database, database)
    audit = configure_database(database, images_name)

    root = source_tree.getroot()
    values = {
        "Name": PROJECT_NAME,
        "Description": (
            "Development fixture for PLOT Individual, Job, and Comparison risk views."
        ),
        "DatabaseName": database_name,
        "DatabasePath": f"{data_name}/{database_name}",
        "ProjectPath": PROJECT_NAME,
        "ProjectFolder": PROJECT_NAME,
        "DataPath": data_name,
        "ImagesPath": images_name,
    }
    for tag, value in values.items():
        element = root.find(tag)
        if element is None:
            element = ET.SubElement(root, tag)
        element.text = value
    ET.indent(source_tree, space="  ")
    source_tree.write(output, encoding="utf-8", xml_declaration=True)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    audit = build_project(args.source, args.output, force=args.force)
    print(f"Created {args.output.resolve()}")
    print(
        f"Classified {audit['assessments']} current assessments across "
        f"{audit['contexts']} contexts and {audit['placements']} active placements."
    )
    print(f"Worker {audit['square_worker']} has sex/gender not provided.")


if __name__ == "__main__":
    main()
