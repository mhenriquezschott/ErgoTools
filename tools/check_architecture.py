"""Enforce package dependency direction without executing inspected modules.

Developer quality gate: AST inspection covers every maintained application module,
including unimported paths. It checks portable core dependencies, renderer/storage
boundaries and exclusion of the separately removable migration utility. The gate reports
source locations; it neither imports application code nor repairs files.

Developer tooling layer; no normal application module imports this file. External
conversion code remains separately removable. This file owns only the operations
described above; it never changes original project files.
"""

import ast
import re
import sys
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path

# Repository location and approved layer/capability policy; no user paths are read.
# Resolved repository root for this developer gate, independent of the launch directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Application source-package root inspected by default; no imports are executed.
PACKAGE_ROOT = PROJECT_ROOT / "src" / "ergotools"
# Approved dependency directions; the composition root is handled separately.
ALLOWED_LAYERS = {
    "domain": {"domain"},
    "application": {"application", "domain"},
    "infrastructure": {"infrastructure", "application", "domain", "resources"},
    "presentation": {"presentation", "application", "domain"},
    "resources": {"resources"},
}
# Even standard-library I/O/dynamic/runtime capabilities excluded from the portable
# domain/application core.
CORE_CAPABILITIES = {
    "sqlite3",
    "tkinter",
    "subprocess",
    "ctypes",
    "socket",
    "urllib",
    "importlib",
}
# VTK import roots restricted to the explicitly named renderer adapters.
RENDERER_MODULES = {"vtk", "vtkmodules"}
# Desktop/plot/render libraries permitted only in presentation and the composition root.
DESKTOP_ONLY = {"PyQt5", "PyQt6", "PySide6", "matplotlib", *RENDERER_MODULES}
# Storage and optimization libraries forbidden in presentation; application ports own
# those interactions.
UI_FORBIDDEN = {"sqlite3", "pulp", "pyomo", "highspy"}


@dataclass(frozen=True)
class Violation:
    """A source location and actionable architecture violation description.

    Attributes:
        module: Qualified inspected application module used for locating the dependency
            boundary.
        line: One-based source line containing the violation.
        message: Actionable architecture diagnostic; no module is imported or repaired.
    """

    module: str
    line: int
    message: str


def inspect_source(
    source: str, module: str, *, is_package: bool = False
) -> list[Violation]:
    """Inspect static imports and explicit dynamic-import escape routes.

    Args:
        source: UTF-8 Python source supplied by the caller, never executed here.
        module: Qualified application module name for resolving layer ownership.
        is_package: Whether relative imports resolve from this module itself.

    Returns:
        Located violations; an empty list means the checked static rules pass. This does
        not certify runtime behavior or semantic documentation quality.

    Raises:
        SyntaxError: The supplied source cannot be parsed as Python.
    """
    tree = ast.parse(source)
    layer = module.split(".")[1] if "." in module else ""
    violations: list[Violation] = []
    package = module if is_package else module.rpartition(".")[0]
    aliases: dict[str, str] = {}

    for node in ast.walk(tree):
        targets: list[str] = []
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".")[0]] = (
                    alias.name if alias.asname else alias.name.split(".")[0]
                )
        elif isinstance(node, ast.ImportFrom):
            target = node.module or ""
            if node.level:
                try:
                    target = resolve_name("." * node.level + target, package)
                except (ImportError, ValueError):
                    violations.append(
                        Violation(module, node.lineno, "Invalid relative import")
                    )
                    continue
            targets = [target]
            for alias in node.names:
                if alias.name == "*":
                    violations.append(Violation(module, node.lineno, "Wildcard import"))
                else:
                    qualified = f"{target}.{alias.name}"
                    targets.append(qualified)
                    aliases[alias.asname or alias.name] = qualified
        else:
            continue
        for target in targets:
            if (
                target == "ergotools_migration"
                or target.startswith("ergotools_migration.")
                or target == "tools.project_migration"
                or target.startswith("tools.project_migration.")
                or target.startswith("ergotools.infrastructure.legacy_")
                or target.startswith("ergotools.infrastructure.archived_results")
            ):
                violations.append(
                    Violation(
                        module,
                        node.lineno,
                        f"Application cannot import the external converter: {target}",
                    )
                )
            top = target.split(".")[0]
            target_parts = target.split(".")
            target_layer = target_parts[1] if len(target_parts) > 1 else ""
            if (
                top == "ergotools"
                and layer in ALLOWED_LAYERS
                and target_layer
                and target_layer not in ALLOWED_LAYERS[layer]
            ):
                violations.append(
                    Violation(
                        module, node.lineno, f"Forbidden layer dependency: {target}"
                    )
                )
            if (
                layer in {"domain", "application"}
                and top != "ergotools"
                and (top not in sys.stdlib_module_names or top in CORE_CAPABILITIES)
            ):
                violations.append(
                    Violation(
                        module,
                        node.lineno,
                        f"Core dependency is not portable: {target}",
                    )
                )
            if (
                top in DESKTOP_ONLY
                and layer != "presentation"
                and module != "ergotools.bootstrap"
            ):
                violations.append(
                    Violation(
                        module,
                        node.lineno,
                        f"Desktop dependency outside presentation: {target}",
                    )
                )
            if top in RENDERER_MODULES and not module.startswith(
                "ergotools.presentation.desktop.rendering.vtk_"
            ):
                violations.append(
                    Violation(
                        module,
                        node.lineno,
                        f"VTK must stay inside its rendering adapter: {target}",
                    )
                )
            if layer == "presentation" and top in UI_FORBIDDEN:
                violations.append(
                    Violation(
                        module,
                        node.lineno,
                        f"UI cannot access storage or optimization: {target}",
                    )
                )

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            first, separator, remainder = name.partition(".")
            resolved = aliases.get(first, first) + (
                separator + remainder if separator else ""
            )
            if resolved in {
                "__import__",
                "builtins.__import__",
                "importlib.import_module",
            }:
                violations.append(
                    Violation(
                        module,
                        node.lineno,
                        "Dynamic imports require an explicit reviewed adapter",
                    )
                )
    return violations


def inspect_package(package_root: Path = PACKAGE_ROOT) -> list[Violation]:
    """Check all application files, including files not reached by tests.

    Args:
        package_root: Application package directory; defaults to this repository.

    Returns:
        Import, naming and forbidden converter-file violations in path order.

    Raises:
        OSError: A source file cannot be read.
        SyntaxError: A maintained source file cannot be parsed.
    """
    violations = []
    for path in sorted(package_root.rglob("*.py")):
        if path.name.startswith("legacy_") or path.name == "archived_results.py":
            violations.append(
                Violation(
                    str(path), 1, "Converter files belong outside the application"
                )
            )
        relative = path.relative_to(package_root.parent).with_suffix("")
        parts = relative.parts
        is_package = parts[-1] == "__init__"
        module = ".".join(parts[:-1] if is_package else parts)
        if any(not re.fullmatch(r"[a-z][a-z0-9_]*|__init__", part) for part in parts):
            violations.append(
                Violation(module, 1, "Module/package names must be snake_case")
            )
        violations.extend(
            inspect_source(
                path.read_text(encoding="utf-8"), module, is_package=is_package
            )
        )
    return violations


def main() -> int:
    """Run the repository architecture gate and report diagnostics to stdout.

    Args:
        None.

    Returns:
        Zero when every checked boundary passes, one when violations are found.

    Raises:
        OSError: Source files cannot be read.
        SyntaxError: A maintained source file is invalid Python.
    """
    violations = inspect_package()
    for violation in violations:
        print(f"{violation.module}:{violation.line}: {violation.message}")
    print(f"Architecture: {len(violations)} violation(s)")
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
