"""Invoke an optional external migration utility without importing its code.

Infrastructure adapter for the application ProjectConversion port. This module
recognizes file/container headers and dispatches a subprocess; it never reads original
assessment tables, converts selectors or decodes archived databases. The source-tree
utility is optional and excluded from the application wheel. Native project opening,
editing and saving do not invoke this adapter's process.

Infrastructure layer. Keep these representations and concrete I/O outside the
domain/application core. Ownership, validation and transaction effects are documented at
each boundary below; no GUI or scientific formula is implemented here.
"""

import os
import shlex
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


class ExternalProjectMigration:
    """Keep process execution separate from native storage and desktop policy."""

    def __init__(self, command: tuple[str, ...] | None = None) -> None:
        """Choose the external executable without running it or importing it.

        Args:
            command: Explicit executable/arguments, or None to find the separately
                installed command and then the optional repository tool.

        Returns:
            None. The resolved command is retained for later explicit conversion.
        """
        executable = shutil.which("ergotools-migrate")
        script = (
            Path(__file__).resolve().parents[3]
            / "tools/project_migration/migrate_project.py"
        )
        self.command = command or (
            (executable,) if executable else (sys.executable, str(script))
        )

    def requires_conversion(self, location: str) -> bool:
        """Recognize unsupported containers without decoding original data.

        Args:
            location: Existing file selected by the owner's Open workflow.

        Returns:
            True for XML descriptors or earlier full native formats 8-17. Other files
            are validated by native Open.

        Raises:
            OSError: The selected file cannot be read.
            sqlite3.Error: A SQLite container has invalid format metadata.
        """
        path = Path(location)
        with path.open("rb") as stream:
            prefix = stream.read(512)
        if prefix.removeprefix(b"\xef\xbb\xbf").lstrip().startswith(b"<"):
            return True
        if prefix.startswith(b"SQLite format 3\x00"):
            connection = sqlite3.connect(
                path.absolute().as_uri() + "?mode=ro", uri=True
            )
            try:
                row = connection.execute(
                    "SELECT version FROM project_metadata"
                ).fetchone()
                return row is not None and row[0] in (
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
                )
            finally:
                connection.close()
        return False

    def command_line(self, source: str, destination: str) -> str:
        """Format terminal guidance using the actual optional tool command.

        Args:
            source: Literal earlier-project path, possibly containing spaces.
            destination: Literal separate output path; never executed here.

        Returns:
            Windows command-line quoting on Windows, POSIX quoting otherwise. The GUI
            launches the same arguments directly without a shell.
        """
        arguments = [*self.command, source, "--output", destination]
        return (
            subprocess.list2cmdline(arguments)
            if os.name == "nt"
            else shlex.join(arguments)
        )

    def convert(self, source: str, destination: str) -> None:
        """Run the removable tool with literal arguments and surface its result.

        No shell interpolation, database conversion or implicit Save occurs here. The
        caller owns destination choice, dirty consent and UI error reporting.

        Args:
            source: Existing input project; the external utility preserves it.
            destination: Separate nonexistent native output path.

        Returns:
            None after the utility successfully publishes and closes its output.

        Raises:
            OSError: The utility cannot be launched or source/output I/O fails.
            ValueError: The utility reports conversion/validation failure.
        """
        completed = subprocess.run(
            [*self.command, source, "--output", destination],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if completed.returncode:
            raise ValueError(
                completed.stderr.strip() or "External project migration failed."
            )
