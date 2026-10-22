"""Verify self-contained assets and reference fidelity.

Test layer. Characterize the contracts named below using immutable inputs, controlled
adapters or disposable projects. Native Qt cases drive owned real controls; scheduled
callbacks surface assertions to the enclosing test. Fixtures/fault injection never
modify the reference application or approved dependency baseline.
"""

import hashlib
import json
import unittest
from importlib.resources import files

from ergotools.infrastructure.resources import read_asset


class ResourceTests(unittest.TestCase):
    """Ensure all migrated resources match their reference bytes."""

    def test_every_asset_matches_the_reference_manifest(self) -> None:
        """Validate every copied icon/model rather than only testing one filename.

        Args:
            None.

        Returns:
            None.
        """
        manifest = json.loads(
            files("ergotools.resources").joinpath("manifest.json").read_text()
        )
        self.assertEqual(len(manifest["assets"]), 71)
        for record in (*manifest["assets"], *manifest.get("derived_assets", ())):
            with self.subTest(asset=record["path"]):
                self.assertEqual(
                    hashlib.sha256(read_asset(record["path"])).hexdigest(),
                    record["sha256"],
                )

    def test_invalid_resource_paths_are_rejected(self) -> None:
        """Reject paths outside the resource namespaces on every platform.

        Args:
            None.

        Returns:
            None.
        """
        for name in (
            "",
            "/icons/save.png",
            "icons/../manifest.json",
            "C:/file",
            "icons\\save.png",
            "unknown/save.png",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                read_asset(name)

    def test_missing_resource_reports_an_error(self) -> None:
        """Do not silently substitute a system-default icon.

        Args:
            None.

        Returns:
            None.
        """
        with self.assertRaises(FileNotFoundError):
            read_asset("icons/not_present.png")
