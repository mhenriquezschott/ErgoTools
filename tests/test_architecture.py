"""Prove the architecture gate rejects forbidden dependencies, not just current code.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import tempfile
import unittest
from pathlib import Path

from tools.check_architecture import inspect_package, inspect_source


class ArchitectureTests(unittest.TestCase):
    """Test real package boundaries and deliberate violations."""

    def test_package_obeys_approved_boundaries(self) -> None:
        """Check every production module, including those not imported in tests.

        Args:
            None.

        Returns:
            None.
        """
        self.assertEqual(inspect_package(), [])

    def test_core_cannot_import_widgets_database_or_solver(self) -> None:
        """Prevent third-party and platform capabilities leaking into the core.

        Args:
            None.

        Returns:
            None.
        """
        for module in ("PyQt5", "sqlite3", "pulp", "vtk", "subprocess"):
            with self.subTest(module=module):
                self.assertTrue(
                    inspect_source(f"import {module}", "ergotools.domain.example")
                )

    def test_application_cannot_import_concrete_infrastructure(self) -> None:
        """Enforce application ports for both absolute and relative imports.

        Args:
            None.

        Returns:
            None.
        """
        for source in (
            "from ergotools.infrastructure import resources",
            "from ..infrastructure import resources",
            "from .. import infrastructure",
        ):
            with self.subTest(source=source):
                self.assertTrue(inspect_source(source, "ergotools.application.example"))

    def test_ui_cannot_query_database(self) -> None:
        """Keep persistence and optimization out of presentation code.

        Args:
            None.

        Returns:
            None.
        """
        for dependency in ("sqlite3", "pulp", "highspy"):
            self.assertTrue(
                inspect_source(
                    f"import {dependency}", "ergotools.presentation.desktop.window"
                )
            )

    def test_vtk_is_restricted_to_its_adapter(self) -> None:
        """Allow a backend replacement without changing arbitrary presentation files.

        Args:
            None.

        Returns:
            None.
        """
        self.assertTrue(
            inspect_source("import vtk", "ergotools.presentation.desktop.window")
        )
        self.assertEqual(
            inspect_source(
                "import vtk", "ergotools.presentation.desktop.rendering.vtk_body"
            ),
            [],
        )

    def test_wildcard_and_dynamic_imports_are_rejected(self) -> None:
        """Do not allow obvious escape routes around dependency checks.

        Args:
            None.

        Returns:
            None.
        """
        for source in (
            "from math import *",
            "__import__('sqlite3')",
            "import importlib as loader\nloader.import_module('sqlite3')",
            "from importlib import import_module as load\nload('sqlite3')",
        ):
            with self.subTest(source=source):
                self.assertTrue(
                    inspect_source(source, "ergotools.infrastructure.example")
                )

    def test_plain_data_and_inward_imports_are_allowed(self) -> None:
        """Avoid blocking the intended pure-domain and application design.

        Args:
            None.

        Returns:
            None.
        """
        source = (
            "from dataclasses import dataclass\n"
            "from ergotools.domain.risk import RiskBand"
        )
        self.assertEqual(inspect_source(source, "ergotools.application.example"), [])

    def test_module_names_are_checked(self) -> None:
        """Catch inconsistent module naming beyond function/class lint checks.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "ergotools"
            package.mkdir()
            (package / "BadName.py").write_text('"""Example."""', encoding="utf-8")
            self.assertTrue(inspect_package(package))

    def test_invalid_relative_import_is_reported(self) -> None:
        """Bad package references should fail the quality gate with a location.

        Args:
            None.

        Returns:
            None.
        """
        self.assertTrue(
            inspect_source("from ....bad import item", "ergotools.domain.example")
        )

    def test_converter_cannot_be_imported_by_application(self) -> None:
        """Reject direct, package-qualified and prior-location converter imports.

        Args:
            None.

        Returns:
            None.
        """
        for source in (
            "import ergotools_migration.legacy_project",
            "from tools import project_migration",
            "from tools.project_migration.ergotools_migration import cli",
            "from ergotools.infrastructure import legacy_project",
            "from ergotools.infrastructure.archived_results import reader",
        ):
            with self.subTest(source=source):
                self.assertTrue(
                    inspect_source(source, "ergotools.infrastructure.example")
                )

    def test_converter_file_cannot_return_to_application(self) -> None:
        """Reject old-schema reader files even when no application imports them.

        Args:
            None.

        Returns:
            None.
        """
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "ergotools"
            package.mkdir()
            (package / "legacy_project.py").write_text(
                '"""Reader."""', encoding="utf-8"
            )
            self.assertTrue(inspect_package(package))
