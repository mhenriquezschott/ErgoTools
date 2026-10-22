"""Negative regression checks for the owned filename and portable collision gate.

Tests supply synthetic paths; no maintained file or original asset is changed. They
distinguish required external conventions from ordinary owned resources.
"""

from pathlib import Path

from tools.check_naming import inspect_paths


def test_owned_resources_and_documents_require_snake_case(tmp_path: Path) -> None:
    """Reject mixed/camel/hyphen names in owned files while accepting clear names.

    Args:
        tmp_path: Synthetic repository root; files need not exist.

    Returns:
        None. Assert every invalid path is located without false valid-name errors.
    """
    paths = [
        tmp_path / name
        for name in (
            "src/ergotools/resources/icons/jobManagement.png",
            "docs/user-guide.md",
            "src/ergotools/resources/models/3dModel.stl",
            "docs/user_guide.md",
            "src/ergotools/resources/icons/job_management.png",
        )
    ]
    violations = inspect_paths(paths, tmp_path)
    assert len(violations) == 3
    assert all("snake_case" in value for value in violations)


def test_external_evidence_and_repository_conventions_are_explicit(
    tmp_path: Path,
) -> None:
    """Retain frozen original names and standard package/entry document spellings.

    Args:
        tmp_path: Synthetic repository root.

    Returns:
        None. Assert only documented external/generated conventions are exempt.
    """
    paths = [
        tmp_path / name
        for name in (
            "docs/reference/OriginalSnapshot.py.txt",
            "test_projects/originals/Old Project_images/Default.png",
            "docs/STATUS.md",
            "tools/README.md",
            "src/ergotools/__init__.py",
        )
    ]
    assert not inspect_paths(paths, tmp_path)


def test_case_insensitive_collisions_are_reported(tmp_path: Path) -> None:
    """Detect names that cannot coexist reliably on common target filesystems.

    Args:
        tmp_path: Synthetic repository root.

    Returns:
        None. Assert the conflicting original spelling is present in diagnostics.
    """
    violations = inspect_paths(
        [tmp_path / "docs/a.md", tmp_path / "docs/A.md"], tmp_path
    )
    assert any("collides" in value for value in violations)
