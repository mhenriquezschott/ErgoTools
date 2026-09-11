#!/usr/bin/env python3
"""Fuse two ErgoTools projects into a development test project."""

import argparse
import shutil
import sqlite3
import xml.etree.ElementTree as ET
from contextlib import closing
from pathlib import Path


TABLE_ORDER = (
    "Worker",
    "Plant",
    "Section",
    "Line",
    "Station",
    "Shift",
    "ErgoTool",
    "WorkerStationShiftErgoTool",
    "LifftResults",
    "DuetResults",
    "TstResults",
    "Job",
    "JobMeasurement",
    "RotationScheme",
    "RotationAssignment",
)


def read_project(project_file):
    project_file = project_file.resolve()
    root = ET.parse(project_file).getroot()
    data_folder = root.findtext("DataPath")
    database_name = root.findtext("DatabaseName")
    images_folder = root.findtext("ImagesPath")
    if not data_folder or not database_name or not images_folder:
        raise ValueError(f"Incomplete project paths in {project_file}")
    return {
        "file": project_file,
        "tree": ET.ElementTree(root),
        "root": root,
        "database": project_file.parent / data_folder / database_name,
        "images": project_file.parent / images_folder,
        "images_name": images_folder,
    }


def table_columns(connection, table):
    return [row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')]


def table_exists(connection, table):
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def merge_database(target_path, source_path):
    audit = {}
    with closing(sqlite3.connect(target_path)) as target, closing(sqlite3.connect(source_path)) as source:
        target.execute("PRAGMA foreign_keys = ON")
        for table in TABLE_ORDER:
            if not table_exists(source, table):
                audit[table] = {"inserted": 0, "conflicts": 0, "source": 0}
                continue
            if not table_exists(target, table):
                raise RuntimeError(f"Target schema is missing required table {table}")

            source_columns = table_columns(source, table)
            target_columns = table_columns(target, table)
            if source_columns != target_columns:
                raise RuntimeError(f"Schema mismatch in table {table}")

            rows = source.execute(f'SELECT * FROM "{table}"').fetchall()
            before = target.total_changes
            placeholders = ", ".join("?" for _ in source_columns)
            columns_sql = ", ".join(f'"{column}"' for column in source_columns)
            target.executemany(
                f'INSERT OR IGNORE INTO "{table}" ({columns_sql}) VALUES ({placeholders})',
                rows,
            )
            inserted = target.total_changes - before
            audit[table] = {
                "inserted": inserted,
                "conflicts": len(rows) - inserted,
                "source": len(rows),
            }

        violations = target.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key validation failed: {violations[:10]}")
        target.commit()
    return audit


def copy_images(source_folder, target_folder):
    copied = 0
    conflicts = 0
    if not source_folder.exists():
        return copied, conflicts
    for source in source_folder.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(source_folder)
        target = target_folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != source.read_bytes():
                raise RuntimeError(f"Different image files use the same path: {relative}")
            conflicts += 1
            continue
        shutil.copy2(source, target)
        copied += 1
    return copied, conflicts


def normalize_image_paths(database_path, new_folder):
    with closing(sqlite3.connect(database_path)) as connection:
        columns = table_columns(connection, "Plant") if table_exists(connection, "Plant") else []
        if "image_path" not in columns or "image_name" not in columns:
            return
        connection.execute(
            """
            UPDATE Plant
            SET image_path = ? || '/' || image_name
            WHERE image_name IS NOT NULL AND trim(image_name) != ''
            """,
            (new_folder,),
        )
        connection.commit()


def update_project_file(project, output_file, project_name, data_name, database_name, images_name):
    root = project["root"]
    values = {
        "Name": project_name,
        "DatabaseName": database_name,
        "DatabasePath": f"{data_name}/{database_name}",
        "ProjectPath": project_name,
        "ProjectFolder": project_name,
        "DataPath": data_name,
        "ImagesPath": images_name,
    }
    for tag, value in values.items():
        element = root.find(tag)
        if element is None:
            element = ET.SubElement(root, tag)
        element.text = value
    ET.indent(project["tree"], space="  ")
    project["tree"].write(output_file, encoding="utf-8", xml_declaration=True)


def fuse_projects(base_file, overlay_file, output_file, project_name, force=False):
    base = read_project(base_file)
    overlay = read_project(overlay_file)
    output_file = output_file.resolve()
    stem = output_file.stem
    data_name = f"{stem}_data"
    images_name = f"{stem}_images"
    database_name = f"{stem}_data.db"
    data_folder = output_file.parent / data_name
    images_folder = output_file.parent / images_name

    outputs = (output_file, data_folder, images_folder)
    if any(path.exists() for path in outputs):
        if not force:
            raise FileExistsError("Output project already exists; use --force to rebuild it")
        for path in outputs:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()

    data_folder.mkdir(parents=True)
    images_folder.mkdir(parents=True)
    output_database = data_folder / database_name
    shutil.copy2(base["database"], output_database)

    audit = merge_database(output_database, overlay["database"])
    base_images = copy_images(base["images"], images_folder)
    overlay_images = copy_images(overlay["images"], images_folder)
    normalize_image_paths(output_database, images_name)
    update_project_file(base, output_file, project_name, data_name, database_name, images_name)

    print(f"Created {output_file}")
    for table, counts in audit.items():
        print(
            f"{table:34} source={counts['source']:4} "
            f"inserted={counts['inserted']:4} conflicts-kept-base={counts['conflicts']:4}"
        )
    print(f"Images from base: copied={base_images[0]}, duplicates={base_images[1]}")
    print(f"Images from overlay: copied={overlay_images[0]}, duplicates={overlay_images[1]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="Project whose records win key conflicts")
    parser.add_argument("overlay", type=Path, help="Project whose distinct records are imported")
    parser.add_argument("output", type=Path, help="Output .ergprj path")
    parser.add_argument("--name", default="ErgoTools Integrated Test", help="Project display name")
    parser.add_argument("--force", action="store_true", help="Replace an existing generated project")
    args = parser.parse_args()
    fuse_projects(args.base, args.overlay, args.output, args.name, args.force)


if __name__ == "__main__":
    main()
