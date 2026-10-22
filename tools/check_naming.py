"""Check owned source, documentation and resource filenames without importing code.

Developer tooling layer: scan maintained files, enforce descriptive snake_case spelling
and identify case-insensitive collisions before packaging. Frozen external
reference/original data and generated outputs retain their required conventions. The
gate reads paths only; it neither renames files nor rewrites user projects.
"""

import re
import sys
from collections.abc import Iterable
from pathlib import Path

# Only maintained roots participate; build evidence/environments are generated.
OWNED_ROOTS = ("src", "tools", "tests", "typings", "docs", "test_projects")
# Repository entry points keep conventional names required by tooling/readers.
CONVENTIONAL_NAMES = {"AGENTS.md", "README.md", "LICENSE.txt", "STATUS.md"}
# These snapshots carry original/external names and must remain byte-identical.
FROZEN_ROOTS = ("docs/reference/", "test_projects/originals/")
# Python package markers are conventional, rather than public descriptive modules.
# Captured reference Python text keeps its source-plus-text archive suffix.
FROZEN_FILES = {"tests/fixtures/reference_plot_load.py.txt"}

# Required Python package entry-point filenames are preserved verbatim.
PACKAGE_MARKERS = {"__init__.py", "__init__.pyi", "__main__.py"}


def inspect_paths(paths: Iterable[Path], root: Path) -> tuple[str, ...]:
    """Validate names and portable uniqueness for caller-supplied owned files.

    Args:
        paths: Existing or synthetic file paths to inspect without opening them.
        root: Repository root used for relative diagnostics and frozen boundaries.

    Returns:
        Located violations; empty when every path follows the naming policy.

    Raises:
        ValueError: A supplied path is outside the repository root.

    Frozen external names are excluded, but ordinary owned documents and assets
    cannot opt out. Names differing only by case are unsafe on Windows/macOS.
    """
    violations = []
    seen: dict[str, str] = {}
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        if (
            relative.startswith(FROZEN_ROOTS)
            or relative in FROZEN_FILES
            or "__pycache__" in path.parts
        ):
            continue
        folded = relative.casefold()
        if folded in seen and seen[folded] != relative:
            violations.append(f"{relative}: collides with {seen[folded]}")
        seen[folded] = relative
        if path.name in CONVENTIONAL_NAMES | PACKAGE_MARKERS:
            continue
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", path.stem):
            violations.append(f"{relative}: owned filenames must use snake_case")
    return tuple(violations)


def maintained_paths(root: Path) -> tuple[Path, ...]:
    """Enumerate owned maintained files while excluding interpreter caches.

    Args:
        root: Repository containing the fixed maintained root directories.

    Returns:
        Stable file paths for source, stubs, tooling, docs and test fixtures.
        Missing roots are harmless for focused/synthetic policy tests.
    """
    return tuple(
        path
        for directory in OWNED_ROOTS
        for path in (root / directory).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )


def main() -> int:
    """Report repository violations for the required local quality gate.

    Args:
        None.

    Returns:
        Zero when naming passes; one after printing each violation to stdout.
    """
    root = Path(__file__).resolve().parents[1]
    violations = inspect_paths(maintained_paths(root), root)
    for violation in violations:
        print(violation)
    print(f"Naming: {len(violations)} violation(s)")
    return int(bool(violations))


if __name__ == "__main__":
    sys.exit(main())
