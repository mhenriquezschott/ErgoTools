"""Keep the documentation review inventory tied to exact maintained source bytes.

Developer tooling layer. This source-only audit complements structural docstring checks:
Section presence cannot certify prose accuracy. The reviewed hash manifest records an
explicit reviewer decision. Regeneration updates locations/contracts and marks
changed/new files pending; it never changes that manifest. This module reads
Python/stubs and shell entry points, never imports inspected application code and never
modifies project databases.
"""

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import cast

from tools.check_documentation import inspect_source, maintained_sources

# Repository-owned audit records; neither is application runtime data.
INVENTORY_PATH = "docs/cleanup_documentation_inventory.json"
# Only an explicit semantic review may update a path's certified source hash.
REVIEW_PATH = "docs/cleanup_documentation_reviews.json"
# Fixed policy text keeps regenerated inventory comparison reproducible.
POLICY = (
    "Structural checks supplement substantive review. Only explicit reviewed-source "
    "hashes certify a file; any edit invalidates its review. Regeneration never "
    "certifies source. Historical inventories remain frozen evidence."
)


def source_hash(path: Path) -> str:
    """Hash exact file bytes, including documentation and comments.

    Args:
        path: Maintained source or shell entry point to read without executing it.

    Returns:
        Lowercase SHA-256 hex digest; line-ending changes also invalidate review.

    Raises:
        OSError: The source cannot be read; no file is silently skipped.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_reviews(path: Path) -> dict[str, str]:
    """Read the explicitly certified path/hash map without accepting malformed data.

    Args:
        path: Reviewer-owned JSON manifest; must already exist.

    Returns:
        Repository-relative POSIX paths mapped to their reviewed source digests.

    Raises:
        ValueError: JSON or its path/digest map is malformed.
        OSError: The manifest cannot be read.
    """
    data: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or any(
        not isinstance(key, str)
        or not isinstance(value, str)
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
        for key, value in data.items()
    ):
        raise ValueError("Review manifest must map source paths to SHA-256 digests")
    return dict(data)


def file_record(path: Path, root: Path, reviews: dict[str, str]) -> dict[str, object]:
    """Inventory every named definition and uppercase constant in one lexical tree.

    Args:
        path: Maintained Python or stub file, including private/nested definitions.
        root: Repository root used to record a portable relative path.
        reviews: Explicit reviewed hashes; absence or mismatch leaves review pending.

    Returns:
        Serializable source, module, symbol, constant and structural-gap evidence.
        Method receiver names are omitted only for actual non-static class methods.

    Raises:
        OSError: Source cannot be read.
        SyntaxError: Python source cannot be parsed.
    """
    relative = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text)
    digest = source_hash(path)
    state = "reviewed_M4" if reviews.get(relative) == digest else "pending_M4"
    symbols: list[dict[str, object]] = []
    constants: list[dict[str, object]] = []

    def visit(owner: ast.AST, prefix: str = "") -> None:
        """Walk lexical owners without confusing nested callbacks with their parents.

        Args:
            owner: Current AST node; its children are visited in source order.
            prefix: Qualified containing definition names followed by a dot.

        Returns:
            None. Append deterministic symbol/constant records to the owned lists.
        """
        for node in ast.iter_child_nodes(owner):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                function = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                parameters: list[str] = []
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    parameters = [
                        arg.arg
                        for arg in (
                            *node.args.posonlyargs,
                            *node.args.args,
                            *([node.args.vararg] if node.args.vararg else []),
                            *node.args.kwonlyargs,
                            *([node.args.kwarg] if node.args.kwarg else []),
                        )
                    ]
                    static = any(
                        isinstance(item, ast.Name) and item.id == "staticmethod"
                        for item in node.decorator_list
                    )
                    if (
                        isinstance(owner, ast.ClassDef)
                        and not static
                        and parameters
                        and parameters[0] in ("self", "cls")
                    ):
                        parameters.pop(0)
                doc = ast.get_docstring(node) or ""
                segment = ast.get_source_segment(text, node) or ""
                symbols.append(
                    {
                        "qualified_name": prefix + node.name,
                        "line": node.lineno,
                        "end_line": node.end_lineno,
                        "kind": "function" if function else "class",
                        "visibility": "private"
                        if node.name.startswith("_")
                        else "public",
                        "has_docstring": bool(doc),
                        "parameters": parameters,
                        "has_args_section": "Args:" in doc,
                        "has_returns_or_yields_section": "Returns:" in doc
                        or "Yields:" in doc,
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "docstring_sha256": hashlib.sha256(doc.encode()).hexdigest(),
                        "documentation_review": state,
                    }
                )
                visit(node, prefix + node.name + ".")
            else:
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        node.targets if isinstance(node, ast.Assign) else [node.target]
                    )
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            prior = (
                                lines[node.lineno - 2].strip()
                                if node.lineno > 1
                                else ""
                            )
                            segment = ast.get_source_segment(text, node) or ""
                            constants.append(
                                {
                                    "qualified_name": prefix + target.id,
                                    "line": node.lineno,
                                    "adjacent_comment": prior
                                    if prior.startswith("#")
                                    else None,
                                    "source_sha256": hashlib.sha256(
                                        segment.encode()
                                    ).hexdigest(),
                                    "documentation_review": state,
                                }
                            )
                visit(node, prefix)

    visit(tree)
    return {
        "path": relative,
        "sha256": digest,
        "has_module_docstring": bool(ast.get_docstring(tree)),
        "file_documentation_review": state,
        "structural_issues": [
            {"line": issue.line, "symbol": issue.symbol, "detail": issue.detail}
            for issue in inspect_source(text, relative)
        ],
        "symbols": symbols,
        "constants": constants,
    }


def build_inventory(root: Path, reviews: dict[str, str]) -> dict[str, object]:
    """Regenerate actual source evidence without approving any missing file review.

    Args:
        root: Repository root containing the maintained code directories.
        reviews: Reviewer-certified hashes read separately from generated inventory.

    Returns:
        Deterministic inventory of Python/stub files and developer shell scripts.
        Changed, added and unreviewed files remain pending even with complete docs.

    Raises:
        OSError: A maintained file cannot be read.
        SyntaxError: A maintained Python/stub file is malformed.
    """
    files = [file_record(path, root, reviews) for path in maintained_sources(root)]
    shells = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": source_hash(path),
            "documentation_review": "reviewed_M4"
            if reviews.get(path.relative_to(root).as_posix()) == source_hash(path)
            else "pending_M4",
        }
        for path in sorted((root / "tools").glob("*.sh"))
    ]
    symbols = [
        symbol
        for file in files
        for symbol in cast(list[dict[str, object]], file["symbols"])
    ]
    functions = [symbol for symbol in symbols if symbol["kind"] == "function"]
    classes = [symbol for symbol in symbols if symbol["kind"] == "class"]
    constants = [
        constant
        for file in files
        for constant in cast(list[dict[str, object]], file["constants"])
    ]
    summary = {
        "python_and_stub_files": len(files),
        "files_reviewed_M4": sum(
            file["file_documentation_review"] == "reviewed_M4" for file in files
        ),
        "files_pending_M4_review": sum(
            file["file_documentation_review"] != "reviewed_M4" for file in files
        ),
        "functions_including_private_and_nested": len(functions),
        "functions_missing_docstring": sum(
            not symbol["has_docstring"] for symbol in functions
        ),
        "functions_with_parameters_missing_args_section": sum(
            bool(symbol["parameters"]) and not symbol["has_args_section"]
            for symbol in functions
        ),
        "functions_missing_return_or_yield_section": sum(
            not symbol["has_returns_or_yields_section"] for symbol in functions
        ),
        "functions_reviewed_M4": sum(
            symbol["documentation_review"] == "reviewed_M4" for symbol in functions
        ),
        "functions_pending_M4_review": sum(
            symbol["documentation_review"] != "reviewed_M4" for symbol in functions
        ),
        "classes_reviewed_M4": sum(
            symbol["documentation_review"] == "reviewed_M4" for symbol in classes
        ),
        "classes_pending_M4_review": sum(
            symbol["documentation_review"] != "reviewed_M4" for symbol in classes
        ),
        "constants_reviewed_M4": sum(
            symbol["documentation_review"] == "reviewed_M4" for symbol in constants
        ),
        "constants_pending_review": sum(
            symbol["documentation_review"] != "reviewed_M4" for symbol in constants
        ),
        "structural_gaps": sum(
            len(cast(list[object], file["structural_issues"])) for file in files
        ),
    }
    return {
        "summary": summary,
        "checkpoint": "M4 documentation review inventory",
        "policy": POLICY,
        "baseline": "cleanup_documentation_baseline.json",
        "files": files,
        "other_maintained_code": shells,
    }


def review_issues(
    root: Path, reviews: dict[str, str], stored: object
) -> tuple[str, ...]:
    """Reject stale inventory, pending certification and orphaned review entries.

    Args:
        root: Repository under audit; inspected code is never imported.
        reviews: Explicit source-hash certification, independently read from disk.
        stored: Parsed generated inventory; malformed or stale metadata cannot pass
            equality.

    Returns:
        Stable diagnostics for every uncertified path plus stale inventory/orphaned
        entries. Even a tampered symbol line/argument/hash makes the inventory stale.

    Raises:
        OSError: Maintained source cannot be read.
        SyntaxError: Maintained source cannot be parsed.
    """
    current = build_inventory(root, reviews)
    paths = (*maintained_sources(root), *sorted((root / "tools").glob("*.sh")))
    names = {path.relative_to(root).as_posix() for path in paths}
    issues = [
        f"{path.relative_to(root).as_posix()}: source needs documentation review"
        for path in paths
        if reviews.get(path.relative_to(root).as_posix()) != source_hash(path)
    ]
    issues.extend(
        f"{name}: obsolete review entry" for name in sorted(set(reviews) - names)
    )
    if stored != current:
        issues.append(
            "Documentation inventory is stale; regenerate after source review"
        )
    return tuple(issues)


def main() -> int:
    """Check review evidence or explicitly refresh metadata without certifying source.

    Args:
        None. --refresh-inventory is read from the command line.

    Returns:
        Zero when every file is certified and inventory matches; one for pending/stale
        evidence. Refresh writes the inventory but still fails for pending reviews.

    Raises:
        OSError: Source, manifest or inventory cannot be read/written.
        ValueError: Audit JSON or the certified hash map is malformed.
        SyntaxError: Maintained source cannot be parsed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-inventory", action="store_true")
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reviews = read_reviews(root / REVIEW_PATH)
    if arguments.refresh_inventory:
        (root / INVENTORY_PATH).write_text(
            json.dumps(build_inventory(root, reviews), indent=2) + "\n",
            encoding="utf-8",
        )
    stored: object = json.loads((root / INVENTORY_PATH).read_text(encoding="utf-8"))
    issues = review_issues(root, reviews, stored)
    for issue in issues:
        print(issue)
    print(f"Documentation review inventory: {len(issues)} issue(s)")
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
