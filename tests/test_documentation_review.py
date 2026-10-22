"""Regressions for documentation inventory drift and explicit review ownership.

Test layer. Tiny temporary repositories exercise the maintained inventory tool without
importing source, opening Qt forms, using reference data or granting semantic approval.
Metadata regeneration must preserve pending reviews rather than certify its own output.
"""

import json
from pathlib import Path

import pytest

from tools.check_documentation_review import (
    build_inventory,
    read_reviews,
    review_issues,
    source_hash,
)


def source_file(root: Path) -> Path:
    """Create one documented synthetic module beneath a maintained source root.

    Args:
        root: Pytest-owned temporary repository; caller owns its cleanup.

    Returns:
        Path to source containing a class method, nested callback and named constant.
        Nothing in that module is executed by this fixture or the inventory tool.
    """
    path = root / "src" / "sample.py"
    path.parent.mkdir(parents=True)
    path.write_text(
        '''"""Synthetic module for lexical inventory regression only."""
# Dimensionless synthetic test value.
VALUE = 1
class Sample:
    """Synthetic method receiver owner."""
    def read(self, value):
        """Return a supplied value through a private helper.

        Args:
            value: Synthetic value to return unchanged.

        Returns:
            The exact supplied value.
        """
        def _inner():
            """Return the enclosing value.

            Args:
                None.

            Returns:
                Enclosing value unchanged.
            """
            return value
        return _inner()
''',
        encoding="utf-8",
    )
    return path


def test_inventory_records_private_nested_and_receiver_contracts(
    tmp_path: Path,
) -> None:
    """Preserve lexical identities and compare generated records exactly.

    Args:
        tmp_path: Disposable repository; fixture source is never imported.

    Returns:
        None. Assert exact symbol names, receiver handling and constant comments.
    """
    path = source_file(tmp_path)
    reviews = {"src/sample.py": source_hash(path)}
    inventory = build_inventory(tmp_path, reviews)
    files = inventory["files"]
    assert isinstance(files, list)
    assert [item["qualified_name"] for item in files[0]["symbols"]] == [
        "Sample",
        "Sample.read",
        "Sample.read._inner",
    ]
    assert files[0]["symbols"][1]["parameters"] == ["value"]
    assert files[0]["constants"][0]["adjacent_comment"].startswith("# Dimensionless")
    assert review_issues(tmp_path, reviews, inventory) == ()


def test_source_and_signature_edits_invalidate_review(tmp_path: Path) -> None:
    """Reject an old certification after a documented signature changes.

    Args:
        tmp_path: Disposable repository whose original bytes are explicitly certified.

    Returns:
        None. Both source-review and stale-inventory diagnostics are required.
    """
    path = source_file(tmp_path)
    reviews = {"src/sample.py": source_hash(path)}
    inventory = build_inventory(tmp_path, reviews)
    path.write_text(path.read_text().replace("self, value", "self, value, extra=None"))
    issues = review_issues(tmp_path, reviews, inventory)
    assert len(issues) == 2
    assert "needs documentation review" in issues[0]
    assert "stale" in issues[1]


def test_refresh_never_certifies_added_or_changed_files(tmp_path: Path) -> None:
    """Keep regenerated metadata pending when the review manifest has no approval.

    Args:
        tmp_path: Disposable repository containing an unreviewed documented module.

    Returns:
        None. Assert regeneration changes no certification and cannot pass review.
    """
    source_file(tmp_path)
    reviews: dict[str, str] = {}
    refreshed = build_inventory(tmp_path, reviews)
    assert reviews == {}
    assert review_issues(tmp_path, reviews, refreshed) == (
        "src/sample.py: source needs documentation review",
    )
    files = refreshed["files"]
    assert isinstance(files, list)
    assert files[0]["file_documentation_review"] == "pending_M4"


def test_symbol_metadata_tampering_is_stale(tmp_path: Path) -> None:
    """Reject changed argument metadata even when file hashes still match.

    Args:
        tmp_path: Disposable certified source and independently mutable inventory.

    Returns:
        None. Assert the whole inventory, including symbol metadata, is checked.
    """
    path = source_file(tmp_path)
    reviews = {"src/sample.py": source_hash(path)}
    stored = build_inventory(tmp_path, reviews)
    files = stored["files"]
    assert isinstance(files, list)
    files[0]["symbols"][1]["parameters"] = ["invented"]
    assert review_issues(tmp_path, reviews, stored) == (
        "Documentation inventory is stale; regenerate after source review",
    )


def test_deleted_source_and_changed_shell_entry_are_detected(tmp_path: Path) -> None:
    """Check shell bytes as well as Python files and reject orphaned approvals.

    Args:
        tmp_path: Disposable repository containing one source and one shell entry.

    Returns:
        None. Assert deleted-source and changed-shell diagnostics remain distinct.
    """
    path = source_file(tmp_path)
    script = tmp_path / "tools" / "run.sh"
    script.parent.mkdir()
    script.write_text("#!/bin/sh\n# Synthetic developer entry.\nexit 0\n")
    reviews = {"src/sample.py": source_hash(path), "tools/run.sh": source_hash(script)}
    stored = build_inventory(tmp_path, reviews)
    path.unlink()
    script.write_text(script.read_text().replace("exit 0", "exit 1"))
    assert review_issues(tmp_path, reviews, stored) == (
        "tools/run.sh: source needs documentation review",
        "src/sample.py: obsolete review entry",
        "Documentation inventory is stale; regenerate after source review",
    )


@pytest.mark.parametrize("payload", [[], {"source": 1}, {"source": "z" * 64}])
def test_malformed_review_manifests_fail_closed(
    tmp_path: Path, payload: object
) -> None:
    """Reject malformed path/hash certification rather than skipping it.

    Args:
        tmp_path: Disposable directory holding the synthetic review JSON.
        payload: Invalid map shape, value type or nonhexadecimal digest scenario.

    Returns:
        None. Assert invalid certification raises a useful ValueError.
    """
    path = tmp_path / "reviews.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="Review manifest"):
        read_reviews(path)


def test_valid_review_manifest_preserves_explicit_hashes(tmp_path: Path) -> None:
    """Read valid certification without adding reviews or changing source.

    Args:
        tmp_path: Disposable directory holding a valid synthetic reviewer decision.

    Returns:
        None. Assert the manifest is returned unchanged.
    """
    path = tmp_path / "reviews.json"
    expected = {"src/sample.py": "a" * 64}
    path.write_text(json.dumps(expected))
    assert read_reviews(path) == expected
