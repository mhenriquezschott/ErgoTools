#!/usr/bin/env python3
"""Print a read-only schema and data inventory for an ErgoTools project."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from database_inventory import inventory_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory an ErgoTools .ergprj file or SQLite .db file without modifying it."
    )
    parser.add_argument("path", help="Path to an .ergprj project or its .db file")
    arguments = parser.parse_args()
    print(inventory_json(arguments.path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

