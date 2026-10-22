"""Audit maintained Python documentation without importing application modules.

Developer tooling layer. Parse source and stubs to locate every named function,
including private and nested helpers, and compare Google-style argument contracts with
their signatures. Result/yield and explicitly escaping error contracts, module purpose,
class documentation and adjacent constant explanations are checked too. These structural
checks cannot judge scientific accuracy or certify a substantive review; the cleanup
inventory records that separate review against source hashes. The inspector is read-only
and also accepts synthetic source for negative tests.
"""

import argparse
import ast
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

# Executable maintained roots and third-party declaration stubs share the policy.
CODE_ROOTS = ("src", "tools", "tests", "typings")
# Entry labels allow documented *args/**kwargs and optional Google type spellings.
ENTRY_LABEL = re.compile(
    r"^([*]{0,2}[A-Za-z_][A-Za-z_0-9.]*)(?:\s*\([^)]*\))?:\s+(.+)$"
)


@dataclass(frozen=True, slots=True)
class DocumentationIssue:
    """Located structural gap; the detail describes a missing contract, not quality.

    Attributes:
        path: Repository-relative file name, or a supplied synthetic diagnostic name.
        line: One-based source line of the owning definition or constant.
        symbol: Dot-qualified owner; <module> identifies the file contract.
        detail: Actionable gap suitable for terminal and inventory diagnostics.
    """

    path: str
    line: int
    symbol: str
    detail: str

    def __str__(self) -> str:
        """Render one stable located diagnostic for the local quality gate.

        Args:
            None.

        Returns:
            File/line, qualified symbol and gap description; no source is included.
        """
        return f"{self.path}:{self.line}: {self.symbol}: {self.detail}"


def _section_lines(doc: str, title: str) -> tuple[str, ...]:
    """Extract one Google section without consuming the following top-level section.

    Args:
        doc: Cleaned docstring returned by ast.get_docstring.
        title: Section title without its colon, such as Args or Returns.

    Returns:
        Section body lines with their relative indentation; empty if absent.
        An indented parameter named Returns cannot terminate an Args section.
    """
    lines = doc.splitlines()
    for index, line in enumerate(lines):
        if line == title + ":":
            end = index + 1
            while end < len(lines) and (
                not lines[end].strip() or lines[end][0].isspace()
            ):
                end += 1
            return tuple(lines[index + 1 : end])
    return ()


def _entry_labels(lines: tuple[str, ...]) -> tuple[str, ...]:
    """Read entry identities at the section's base indentation, preserving repeats.

    Args:
        lines: One section body, including indented continuation paragraphs.

    Returns:
        Argument or exception names without star prefixes. Deeper continuation
        text containing a colon is not interpreted as another parameter.
    """
    populated = [line for line in lines if line.strip()]
    if not populated:
        return ()
    depth = min(len(line) - len(line.lstrip()) for line in populated)
    labels = []
    for line in populated:
        if len(line) - len(line.lstrip()) == depth:
            match = ENTRY_LABEL.fullmatch(line.strip())
            if match:
                labels.append(match[1].lstrip("*"))
    return tuple(labels)


def _own_nodes(node: ast.AST) -> Iterator[ast.AST]:
    """Visit a definition's executable scope without attributing nested contracts.

    Args:
        node: Function or statement subtree whose own yield/raise nodes are needed.

    Yields:
        Descendant nodes excluding nested functions, classes and lambda scopes.
        A yielding nested fixture therefore does not make its enclosing test yield.
    """
    for child in ast.iter_child_nodes(node):
        if isinstance(
            child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
        ):
            continue
        yield child
        yield from _own_nodes(child)


def _parameter_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef, method: bool
) -> tuple[str, ...]:
    """Resolve explicit signature arguments, including positional-only and variadic.

    Args:
        node: Parsed function definition; annotations are not evaluated.
        method: True only when the direct lexical owner is a class.

    Returns:
        Parameter names in declaration order, omitting an actual method receiver.
        Static methods retain their first argument even when it is called self.
    """
    arguments = [*node.args.posonlyargs, *node.args.args]
    static = any(
        isinstance(item, ast.Name) and item.id == "staticmethod"
        for item in node.decorator_list
    )
    if method and not static and arguments and arguments[0].arg in ("self", "cls"):
        arguments = arguments[1:]
    return tuple(
        item.arg
        for item in [
            *arguments,
            *([node.args.vararg] if node.args.vararg else []),
            *node.args.kwonlyargs,
            *([node.args.kwarg] if node.args.kwarg else []),
        ]
    )


def _raised_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Find explicitly raised errors that are not consumed by a local handler.

    Args:
        node: Function scope to inspect without entering nested definitions.

    Returns:
        Explicit exception constructor names, including qualified adapter errors.
        Locally handled exceptions are omitted when the matching handler has no
        bare re-raise. Wrapped errors are documented under their escaping wrapper.
        This conservative static check cannot infer exceptions from called code.
    """
    owned = tuple(_own_nodes(node))
    raised = [item for item in owned if isinstance(item, ast.Raise)]
    result = set()
    for item in raised:
        if not isinstance(item.exc, ast.Call) or not isinstance(
            item.exc.func, (ast.Name, ast.Attribute)
        ):
            continue
        name = ast.unparse(item.exc.func)
        consumed = False
        for block in owned:
            if not isinstance(block, (ast.Try, ast.TryStar)):
                continue
            if not any(
                item is child or item in tuple(_own_nodes(child))
                for child in block.body
            ):
                continue
            for handler in block.handlers:
                names = (
                    tuple(ast.unparse(value) for value in handler.type.elts)
                    if isinstance(handler.type, ast.Tuple)
                    else (ast.unparse(handler.type),)
                    if handler.type
                    else ()
                )
                catches = (
                    handler.type is None
                    or name in names
                    or "BaseException" in names
                    or (
                        "Exception" in names
                        and name
                        not in ("SystemExit", "KeyboardInterrupt", "GeneratorExit")
                    )
                )
                reraises = any(
                    isinstance(value, ast.Raise) and value.exc is None
                    for value in _own_nodes(handler)
                )
                if catches and not reraises:
                    consumed = True
        if not consumed:
            result.add(name)
    return result


def inspect_source(source: str, path: str) -> tuple[DocumentationIssue, ...]:
    """Locate structural documentation gaps in one maintained module or stub.

    Args:
        source: UTF-8-decoded Python source; neither imports nor functions execute.
        path: Repository-relative diagnostic label, also valid for synthetic tests.

    Returns:
        Stable located issues for missing file/class/function contracts, signature
        drift, duplicate argument entries, absent output/known-error descriptions,
        and uppercase assignments lacking an adjacent explanation. An empty result
        proves structural completeness only; semantic review remains separate.

    Raises:
        SyntaxError: The source cannot be parsed by the approved interpreter.
    """
    tree = ast.parse(source, filename=path)
    lines = source.splitlines()
    issues: list[DocumentationIssue] = []
    if not ast.get_docstring(tree):
        issues.append(
            DocumentationIssue(
                path, 1, "<module>", "missing file purpose/scope/layer documentation"
            )
        )

    def visit(owner: ast.AST, prefix: str = "") -> None:
        """Audit lexical owners recursively while retaining precise qualified names.

        Args:
            owner: Current module, class, function or compound statement node.
            prefix: Dot-qualified containing definition names, with trailing dot.

        Returns:
            None. Append located gaps to the enclosing issues list in source order.
        """
        for node in ast.iter_child_nodes(owner):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = prefix + node.name
                doc = ast.get_docstring(node) or ""
                missing = []
                if not doc:
                    missing.append("missing substantive docstring")
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    expected = _parameter_names(node, isinstance(owner, ast.ClassDef))
                    documented = _entry_labels(_section_lines(doc, "Args"))
                    if not _section_lines(doc, "Args"):
                        missing.append(
                            "missing Args section (use None for no explicit arguments)"
                        )
                    if set(expected) != set(documented):
                        missing.append(
                            f"Args mismatch: signature={expected!r}, "
                            f"documented={documented!r}"
                        )
                    if len(documented) != len(set(documented)):
                        missing.append("duplicate Args entries")
                    owned = tuple(_own_nodes(node))
                    output = (
                        "Yields"
                        if any(
                            isinstance(item, (ast.Yield, ast.YieldFrom))
                            for item in owned
                        )
                        else "Returns"
                    )
                    if not any(line.strip() for line in _section_lines(doc, output)):
                        missing.append(f"missing {output} description")
                    raised = _raised_names(node)
                    absent_errors = raised - set(
                        _entry_labels(_section_lines(doc, "Raises"))
                    )
                    if absent_errors:
                        missing.append(
                            "undocumented explicitly escaping errors: "
                            f"{sorted(absent_errors)!r}"
                        )
                for detail in missing:
                    issues.append(
                        DocumentationIssue(path, node.lineno, qualified, detail)
                    )
                visit(node, qualified + ".")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        prior = (
                            lines[node.lineno - 2].strip() if node.lineno > 1 else ""
                        )
                        # A literal '#' in a value is not accepted as a comment.
                        adjacent = prior.startswith("#") and bool(prior.lstrip("# "))
                        if not adjacent:
                            issues.append(
                                DocumentationIssue(
                                    path,
                                    node.lineno,
                                    prefix + target.id,
                                    "constant needs an adjacent "
                                    "meaning/units/source comment",
                                )
                            )
                visit(node, prefix)
            else:
                visit(node, prefix)

    visit(tree)
    return tuple(issues)


def maintained_sources(root: Path) -> tuple[Path, ...]:
    """Enumerate maintained Python and stub files without importing any package.

    Args:
        root: Repository root containing the fixed source/tool/test/stub roots.

    Returns:
        Sorted paths excluding interpreter caches; frozen source-text evidence,
        generated environments and artifacts are outside these executable roots.
    """
    return tuple(
        sorted(
            path
            for name in CODE_ROOTS
            for path in (root / name).rglob("*")
            if path.suffix in (".py", ".pyi") and "__pycache__" not in path.parts
        )
    )


def main() -> int:
    """Report structural gaps for all maintained code or caller-selected files.

    Args:
        None. Optional positional paths come from the command-line argument list.

    Returns:
        Zero on structural success; one after printing gaps. Read/parse errors
        propagate rather than silently skipping an uninspectable maintained file.

    Raises:
        OSError: A selected source file cannot be read.
        SyntaxError: A selected source file is malformed.

    This entry point writes no inventory and never marks a semantic review done.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = tuple(arguments.paths) or maintained_sources(root)
    issues = tuple(
        issue
        for path in paths
        for issue in inspect_source(path.read_text(encoding="utf-8"), path.as_posix())
    )
    for issue in issues:
        print(issue)
    print(f"Documentation structure: {len(issues)} gap(s) in {len(paths)} file(s)")
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
