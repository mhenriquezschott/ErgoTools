"""Executable boundary for the separately removable ErgoTools migration tool.

Run with the approved application interpreter from any working directory. Python adds
this script's directory to module search paths normally; no custom sys.path patch or
application import of conversion code is needed. cli.main owns arguments, read-only
input and exclusive native output; this wrapper only returns its status.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.project_migration.ergotools_migration.cli import main
else:
    from ergotools_migration.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
