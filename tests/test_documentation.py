"""Negative regressions for source-only documentation contract inspection.

Test layer. Synthetic snippets expose missing/private/nested contracts, signature drift
and generator scope without importing or executing the inspected code. These tests prove
structural detection; they do not certify semantic prose quality.
"""

from tools.check_documentation import inspect_source


def test_signature_drift_duplicates_and_variadic_arguments_are_located() -> None:
    """Reject obsolete argument entries even when every section heading exists.

    Args:
        None.

    Returns:
        None. Assert drift and duplicates are located on the offending function.
    """
    source = '''"""Test module: synthetic contracts only."""
def sample(value, /, *items, enabled=False, **options):
    """Inspect values.

    Args:
        value: Value to inspect.
        items: Extra values.
        items: Accidental duplicate.
        obsolete: Removed option.
        options: Named options.

    Returns:
        Inspection result.
    """
    return value
'''
    issues = inspect_source(source, "synthetic.py")
    assert len(issues) == 2
    assert all(issue.symbol == "sample" and issue.line == 2 for issue in issues)
    assert any(
        "enabled" in issue.detail and "obsolete" in issue.detail for issue in issues
    )
    assert any("duplicate" in issue.detail for issue in issues)


def test_private_nested_functions_and_generator_scope_are_independent() -> None:
    """Require nested helper contracts without attributing their yields to owners.

    Args:
        None.

    Returns:
        None. Assert the enclosing ordinary function needs Returns and the nested
        generator needs Yields; both qualified identities are retained.
    """
    source = '''"""Test module: lexical-scope documentation fixture."""
def outer():
    """Build a generator factory.

    Args:
        None.

    Yields:
        Incorrectly attributed nested values.
    """
    def _inner():
        """Produce one number.

        Args:
            None.

        Returns:
            Incorrect section for a generator.
        """
        yield 1
    return _inner
'''
    issues = inspect_source(source, "nested.py")
    assert [(item.symbol, item.detail) for item in issues] == [
        ("outer", "missing Returns description"),
        ("outer._inner", "missing Yields description"),
    ]


def test_receivers_continuations_and_direct_error_contracts() -> None:
    """Distinguish real receivers from static arguments and report missing errors.

    Args:
        None.

    Returns:
        None. Assert valid multiline Args do not invent parameters from a colon
        in continuation prose; the directly raised error is still required.
    """
    source = '''"""Test module: receiver and error contract fixture."""
class Example:
    """Synthetic class with ordinary and static methods."""

    def read(self, value):
        """Read a value.

        Args:
            value (int): Value to inspect, with additional context:
                reason: this is prose, not another parameter.

        Returns:
            Accepted value.
        """
        raise ValueError("rejected")

    @staticmethod
    def static(self):
        """Return the explicit argument named self.

        Args:
            self: An ordinary argument, despite its spelling.

        Returns:
            The supplied argument.
        """
        return self
'''
    issues = inspect_source(source, "receivers.py")
    assert len(issues) == 1
    assert issues[0].symbol == "Example.read"
    assert "ValueError" in issues[0].detail


def test_module_and_adjacent_constant_documentation_cannot_be_faked_by_values() -> None:
    """Reject an undocumented module and a hash character masquerading as a comment.

    Args:
        None.

    Returns:
        None. Assert the located module/constant gaps and acceptance of the
        separately explained dimensionless limit.
    """
    source = """COLOR = "#ffffff"
# Upper inclusive model lookup index, dimensionless.
LIMIT = 200
"""
    issues = inspect_source(source, "constants.py")
    assert [(issue.symbol, issue.line) for issue in issues] == [
        ("<module>", 1),
        ("COLOR", 1),
    ]


def test_handled_errors_require_the_escaping_wrapper_contract() -> None:
    """Avoid demanding a public Raises contract for a consumed internal exception.

    Args:
        None.

    Returns:
        None. Assert the wrapping RuntimeError is located while the locally caught
        ValueError is excluded from the public error requirement.
    """
    source = '''"""Test module: handled-error contract fixture."""
def wrapped():
    """Translate an internal failure.

    Args:
        None.

    Returns:
        None on a successful path.
    """
    try:
        raise ValueError("internal")
    except ValueError as error:
        raise RuntimeError("public") from error
'''
    issues = inspect_source(source, "wrapped.py")
    assert len(issues) == 1
    assert "RuntimeError" in issues[0].detail
    assert "ValueError" not in issues[0].detail


def test_bare_reraise_preserves_the_original_error_contract() -> None:
    """Require a documented error when a matching handler propagates it unchanged.

    Args:
        None.

    Returns:
        None. Assert a cleanup-and-reraise block does not hide the original error
        from structural inspection.
    """
    source = '''"""Test module: cleanup-and-reraise fixture."""
def checked():
    """Propagate an original failure after cleanup.

    Args:
        None.

    Returns:
        None on a successful path.
    """
    try:
        raise ValueError("invalid source")
    except BaseException:
        raise
'''
    issues = inspect_source(source, "reraise.py")
    assert len(issues) == 1
    assert "ValueError" in issues[0].detail
