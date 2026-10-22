"""Command-line boundary for the removable project migration utility.

Tools-layer composition only. It chooses XML conversion or earlier native upgrade,
publishes a separate native document and reports success/error as UTF-8 JSON. It neither
launches Qt nor modifies preferences, recent projects or originals. The installed
ErgoTools application supplies the native writer and approved dependencies. This utility
is not included in the application wheel.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

import argparse
import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import uuid4

from ergotools.application.session import DocumentKey

from .legacy_conversion import convert_legacy_project
from .previous_project import upgrade_previous_project


def main(argv: list[str] | None = None) -> int:
    """Convert an explicit source into one standalone native project file.

    The source is never overwritten. Structured stdout reports the destination, native
    format and counts; stderr reports failures. Original data remains at the supplied
    source, outside the usable standalone output project.

    Args:
        argv: CLI arguments without program name; None uses the current process.

    Returns:
        Zero after successful publication; one for reported input/conversion failures.
        argparse handles help/invalid syntax with its standard exits.

    Raises:
        SystemExit: Help was requested or required CLI arguments are invalid.
    """
    parser = argparse.ArgumentParser(
        description="Migrate an old ErgoTools project to a separate native file."
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Original XML or earlier full native format 8-18 project",
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Nonexistent native destination"
    )
    arguments = parser.parse_args(argv)
    try:
        with arguments.source.open("rb") as stream:
            prefix = stream.read(512)
        project = (
            convert_legacy_project(arguments.source, arguments.output, uuid4().hex)
            if prefix.removeprefix(b"\xef\xbb\xbf").lstrip().startswith(b"<")
            else upgrade_previous_project(arguments.source, arguments.output)
        )
        with project:
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "output": str(arguments.output.absolute()),
                        "format": project.format_version,
                        "assessments": len(project.list_assessments()),
                        "plants": len(project.load_hierarchy().plants),
                        "rotations": len(project.load_rotation_schemes()),
                        "results": sum(
                            project.load_saved_result(
                                DocumentKey(
                                    project.metadata.project_id, item.document_id
                                )
                            )
                            is not None
                            for item in project.load_history().entries
                        ),
                    }
                )
            )
        return 0
    except (OSError, ValueError, sqlite3.Error, ET.ParseError) as error:
        print(json.dumps({"status": "error", "message": str(error)}), file=sys.stderr)
        return 1
